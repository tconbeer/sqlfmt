import re
from typing import TYPE_CHECKING, Callable, List, Optional, Type

from sqlfmt.comment import Comment
from sqlfmt.exception import (
    SqlfmtBracketError,
    SqlfmtControlFlowException,
    StopJinjaLexing,
)
from sqlfmt.line import Line
from sqlfmt.node import Node, get_previous_token
from sqlfmt.rule import MAYBE_WHITESPACES, Rule
from sqlfmt.token import Token, TokenType

if TYPE_CHECKING:
    from sqlfmt.analyzer import Analyzer


def group(*choices: str) -> str:
    """
    Convenience function for creating grouped alternatives in regex
    """
    return f"({'|'.join(choices)})"


# return a human-readable token from a regex pattern
def simplify_jinja_regex(pattern: str) -> str:
    replacements = [
        ("\\{", "{"),
        ("\\}", "}"),
        ("-?", ""),
        ("\\s*", " "),
    ]
    for old, new in replacements:
        pattern = pattern.replace(old, new)
    return pattern


def raise_sqlfmt_bracket_error(
    _: "Analyzer", source_string: str, match: re.Match
) -> None:
    spos, epos = match.span(1)
    raw_token = source_string[spos:epos]
    raise SqlfmtBracketError(
        f"Encountered closing bracket '{raw_token}' at position"
        f" {spos}, before matching opening bracket. Context:"
        f" {source_string[spos:spos+50]}"
    )


def add_node_to_buffer(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    token_type: TokenType,
    previous_node: Optional[Node] = None,
    override_analyzer_prev_node: bool = False,
) -> None:
    """
    Create a token of token_type from the match, then create a Node
    from that token and append it to the Analyzer's buffer
    """
    if previous_node is None and override_analyzer_prev_node is False:
        previous_node = analyzer.previous_node
    token = Token.from_match(source_string, match, token_type)
    node = analyzer.node_manager.create_node(token=token, previous_node=previous_node)
    analyzer.node_buffer.append(node)
    analyzer.pos = token.epos


def safe_add_node_to_buffer(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    token_type: TokenType,
    fallback_token_type: TokenType,
) -> None:
    """
    Try to create a token of token_type from the match; if that fails
    with a SqlfmtBracketError, create a token of fallback_token_type.
    Then create a Node from that token and append it to the Analyzer's buffer
    """
    try:
        add_node_to_buffer(analyzer, source_string, match, token_type)
    except SqlfmtBracketError:
        add_node_to_buffer(analyzer, source_string, match, fallback_token_type)


def add_comment_to_buffer(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    Create a COMMENT token from the match, then create a Comment
    from that token and append it to the Analyzer's buffer
    """
    token = Token.from_match(source_string, match, TokenType.COMMENT)
    is_standalone = (not bool(analyzer.node_buffer)) or "\n" in token.token
    comment = Comment(token=token, is_standalone=is_standalone)
    analyzer.comment_buffer.append(comment)
    analyzer.pos = token.epos


def add_jinja_comment_to_buffer(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    Create a COMMENT token from the match, then create a Comment
    from that token and append it to the Analyzer's buffer; raise
    StopJinjaLexing to revert to SQL lexing
    """
    add_comment_to_buffer(analyzer, source_string, match)
    raise StopJinjaLexing


def handle_newline(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    When a newline is encountered in the source, we typically want to create a
    new line in the Analyzer's line_buffer, flushing the node_buffer and
    comment_buffer in the process.

    However, if we have lexed a standalone comment, we do not want to create
    a Line with only that comment; instead, it must be added to the next Line
    that contains Nodes
    """
    nl_token = Token.from_match(source_string, match, TokenType.NEWLINE)
    nl_node = analyzer.node_manager.create_node(
        token=nl_token, previous_node=analyzer.previous_node
    )
    if analyzer.node_buffer or not analyzer.comment_buffer:
        analyzer.node_buffer.append(nl_node)
        analyzer.line_buffer.append(
            Line.from_nodes(
                previous_node=analyzer.previous_line_node,
                nodes=analyzer.node_buffer,
                comments=analyzer.comment_buffer,
            )
        )
        analyzer.node_buffer = []
        analyzer.comment_buffer = []
    else:
        # standalone comments; don't create a line, since
        # these need to be attached to the next line with
        # contents
        pass
    analyzer.pos = nl_token.epos


def handle_semicolon(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    When we hit a semicolon, the next token may require a different rule set,
    so we need to reset the analyzer's rule stack, if new rules have been
    pushed
    """
    if analyzer.rule_stack:
        analyzer.rules = analyzer.rule_stack[0]
        analyzer.rule_stack = []

    add_node_to_buffer(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        token_type=TokenType.SEMICOLON,
    )


def handle_ddl_as(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    When we hit "as" in a create function or table statement,
    the following syntax should be parsed using the main (select) rules,
    unless the next token is a quoted name.
    """
    add_node_to_buffer(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        token_type=TokenType.UNTERM_KEYWORD,
    )

    quoted_name_rule = analyzer.get_rule("quoted_name")
    comment_rule = analyzer.get_rule("comment")

    quoted_name_pattern = rf"({comment_rule.pattern}|\s)*" + quoted_name_rule.pattern
    quoted_name_match = re.match(
        quoted_name_pattern, source_string[analyzer.pos :], re.IGNORECASE | re.DOTALL
    )

    if not quoted_name_match:
        assert analyzer.rule_stack, (
            "Internal Error! Open an issue. Could not parse DDL 'as' "
            f"at pos {analyzer.pos}. Context: "
            f"{source_string[analyzer.pos :analyzer.pos+50]}"
        )
        analyzer.pop_rules()


def handle_closing_angle_bracket(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    When we hit ">", it could be a closing bracket, the ">" operator,
    or the first character of another operator, like ">>". We need
    to first assume it's a closing bracket, but if that raises a lexing
    error, we need to try to match the source again against the operator
    rule, to get the whole operator token
    """
    try:
        add_node_to_buffer(
            analyzer=analyzer,
            source_string=source_string,
            match=match,
            token_type=TokenType.BRACKET_CLOSE,
        )
    except SqlfmtBracketError:
        operator_rule = analyzer.get_rule("operator")
        operator_pattern = re.compile(
            r"\s*" + operator_rule.pattern,
            re.IGNORECASE | re.DOTALL,
        )
        operator_match = operator_pattern.match(source_string, analyzer.pos)

        assert operator_match, (
            "Internal Error! Open an issue. Could not parse closing bracket '>' "
            f"at pos {analyzer.pos}. Context: "
            f"{source_string[analyzer.pos :analyzer.pos+10]}"
        )
        add_node_to_buffer(
            analyzer=analyzer,
            source_string=source_string,
            match=operator_match,
            token_type=TokenType.OPERATOR,
        )


def handle_set_operator(
    analyzer: "Analyzer", source_string: str, match: re.Match
) -> None:
    """
    Mostly, when we encounter a set operator (like union) we just want to add
    a token with a SET_OPERATOR type. However, EXCEPT is an overloaded
    keyword in some dialects (BigQuery) that support `select * except (fields)`.
    In this case, except should be a WORD_OPERATOR
    """
    previous_node = analyzer.previous_node
    token = Token.from_match(source_string, match, TokenType.SET_OPERATOR)
    prev_token, _ = get_previous_token(previous_node)
    if (
        token.token.lower() == "except"
        and prev_token
        and prev_token.type is TokenType.STAR
    ):
        token = Token(
            type=TokenType.WORD_OPERATOR,
            prefix=token.prefix,
            token=token.token,
            spos=token.spos,
            epos=token.epos,
        )
    node = analyzer.node_manager.create_node(token=token, previous_node=previous_node)
    analyzer.node_buffer.append(node)
    analyzer.pos = token.epos


def handle_number(analyzer: "Analyzer", source_string: str, match: re.Match) -> None:
    """
    We don't know if a token like "-3" or "+4" is properly a unary operator,
    or a poorly-spaced binary operator, so we have to check the previous
    node.
    """
    first_char = source_string[match.span(1)[0] : match.span(1)[0] + 1]
    if first_char in ["+", "-"] and analyzer.previous_node:
        prev_token, _ = get_previous_token(analyzer.previous_node)
        if prev_token and prev_token.type in (
            TokenType.NUMBER,
            TokenType.NAME,
            TokenType.QUOTED_NAME,
            TokenType.STATEMENT_END,
            TokenType.BRACKET_CLOSE,
        ):
            # This is a binary operator. Create a new match for only the
            # operator token
            op_prog = re.compile(r"\s*(\+|-)")
            op_match = op_prog.match(source_string, pos=analyzer.pos)
            assert op_match, "Internal error! Could not match symbol of binary operator"
            add_node_to_buffer(
                analyzer=analyzer,
                source_string=source_string,
                match=op_match,
                token_type=TokenType.OPERATOR,
            )
            # we don't have to handle the rest of the number; this
            # will get called again by analyzer.lex
            return

    # in all other cases, this is a number with/out a unary operator, and we lex it
    # as a single token
    add_node_to_buffer(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        token_type=TokenType.NUMBER,
    )


def handle_nonreserved_keyword(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    action: Callable[["Analyzer", str, re.Match], None],
) -> None:
    """
    Checks to see if we're at depth 0 (assuming this is a name); if so, then take the
    passed action, otherwise lex it as a name.
    """
    token = Token.from_match(source_string, match, token_type=TokenType.NAME)
    node = analyzer.node_manager.create_node(
        token=token, previous_node=analyzer.previous_node
    )
    if node.depth[0] > 0:
        analyzer.node_buffer.append(node)
        analyzer.pos = token.epos
    else:
        action(analyzer, source_string, match)


def lex_ruleset(
    analyzer: "Analyzer",
    source_string: str,
    _: re.Match,
    new_ruleset: List["Rule"],
    stop_exception: Type[SqlfmtControlFlowException],
) -> None:
    """
    Makes a nested call to analyzer.lex, with the new ruleset activated.
    """
    analyzer.push_rules(new_ruleset)
    try:
        analyzer.lex(source_string)
    except stop_exception:
        analyzer.pop_rules()


def handle_jinja_data_block(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    end_rule_name: str,
) -> None:
    """
    A set block, like {% set my_var %}data{% endset %} should be parsed
    as a single DATA token... the data between the two tags need not be
    sql or python, and should not be formatted.
    """
    # find the ending tag
    end_rule = analyzer.get_rule(rule_name=end_rule_name)
    end_match = end_rule.program.search(source_string, pos=analyzer.pos)
    if end_match is None:
        spos, epos = match.span(1)
        raw_token = source_string[spos:epos]
        raise SqlfmtBracketError(
            f"Encountered unterminated Jinja set or call block '{raw_token}' at "
            f"position {spos}. Expected end tag: "
            f"{simplify_jinja_regex(end_rule.pattern)}"
        )
    # the data token is everything between the start and end tags, inclusive
    data_spos = match.span(1)[0]
    data_epos = end_match.span(1)[1]
    data_token = Token(
        type=TokenType.DATA,
        prefix=source_string[analyzer.pos : data_spos],
        token=source_string[data_spos:data_epos],
        spos=data_spos,
        epos=data_epos,
    )
    data_node = analyzer.node_manager.create_node(
        token=data_token, previous_node=analyzer.previous_node
    )
    analyzer.node_buffer.append(data_node)
    analyzer.pos = data_epos
    raise StopJinjaLexing


def handle_jinja_block(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    start_name: str,
    end_name: str,
    other_names: List[str],
    end_reset_sql_depth: bool = False,
) -> None:
    """
    An if block, like {% if cond %}code{% else %}other_code{% endif %}
    needs special handling, since the depth of the jinja tags is determined
    by the code they contain.
    """
    # for some jinja blocks, we need to reset the state after each branch
    previous_node = analyzer.previous_node
    # add the start tag to the buffer
    add_node_to_buffer(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        token_type=TokenType.JINJA_BLOCK_START,
    )

    # configure the block parser
    start_rule = analyzer.get_rule(rule_name=start_name)
    end_rule = analyzer.get_rule(rule_name=end_name)
    other_rules = [analyzer.get_rule(rule_name=r) for r in other_names]
    patterns = [start_rule.pattern, end_rule.pattern] + [r.pattern for r in other_rules]
    program = re.compile(
        MAYBE_WHITESPACES + group(*patterns), re.IGNORECASE | re.DOTALL
    )

    while True:
        # search ahead for the next matching control tag
        next_tag_match = program.search(source_string, analyzer.pos)
        if not next_tag_match:

            raise SqlfmtBracketError(
                f"Encountered unterminated Jinja block at position"
                f" {match.span(0)[0]}. Expected end tag: "
                f"{simplify_jinja_regex(end_rule.pattern)}"
            )
        # otherwise, if the tag matches, lex everything up to that token
        # using the ruleset that was active before jinja
        next_tag_pos = next_tag_match.span(0)[0]
        jinja_rules = analyzer.pop_rules()
        analyzer.stops.append(next_tag_pos)
        try:
            analyzer.lex(source_string)
        except StopIteration:
            analyzer.stops.pop()

        analyzer.push_rules(jinja_rules)
        # it is possible for the next_tag_match found above to have already been lexed.
        # but if it hasn't, we need to process it
        if analyzer.pos == next_tag_pos:
            # if this is another start tag, we have nested jinja blocks,
            # so we recurse a level deeper
            if start_rule.program.match(source_string, analyzer.pos):
                try:
                    handle_jinja_block(
                        analyzer=analyzer,
                        source_string=source_string,
                        match=next_tag_match,
                        start_name=start_name,
                        end_name=end_name,
                        other_names=other_names,
                    )
                except StopJinjaLexing:
                    continue
            # if this the tag that ends the block, add it to the
            # buffer
            elif end_rule.program.match(source_string, analyzer.pos):
                add_node_to_buffer(
                    analyzer=analyzer,
                    source_string=source_string,
                    match=next_tag_match,
                    token_type=TokenType.JINJA_BLOCK_END,
                )
                if end_reset_sql_depth and analyzer.previous_node:
                    if previous_node:
                        analyzer.previous_node.open_brackets = (
                            previous_node.open_brackets.copy()
                        )
                    else:
                        analyzer.previous_node.open_brackets = []
                break
            # otherwise, this is an elif or else statement; we add it to
            # the buffer, but with the previous node set to the node before
            # the if statement (to reset the depth)
            else:
                add_node_to_buffer(
                    analyzer=analyzer,
                    source_string=source_string,
                    match=next_tag_match,
                    token_type=TokenType.JINJA_BLOCK_KEYWORD,
                    previous_node=previous_node,
                    override_analyzer_prev_node=True,
                )
        else:
            continue

    raise StopJinjaLexing


def handle_jinja(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    start_name: str,
    end_name: str,
    token_type: TokenType,
) -> None:
    """
    Lex simple jinja statements and expressions (with possibly nested curlies)
    and add to buffer
    """
    handle_potentially_nested_tokens(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        start_name=start_name,
        end_name=end_name,
        token_type=token_type,
    )
    raise StopJinjaLexing


def handle_potentially_nested_tokens(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    start_name: str,
    end_name: str,
    token_type: TokenType,
) -> None:
    # extract properties from matching start of token
    """
    Lex potentially nested statements, like jinja statements or
    c-style block comments
    """
    start_rule = analyzer.get_rule(rule_name=start_name)
    end_rule = analyzer.get_rule(rule_name=end_name)
    # extract properties from matching start of token
    pos, _ = match.span(0)
    spos, epos = match.span(1)
    prefix = source_string[pos:spos]
    # construct a new regex that will match the first instance
    # of either the ending or nesting rules
    patterns = [start_rule.pattern, end_rule.pattern]
    program = re.compile(
        MAYBE_WHITESPACES + group(*patterns), re.IGNORECASE | re.DOTALL
    )
    epos = analyzer.search_for_terminating_token(
        start_rule=start_name,
        program=program,
        nesting_program=start_rule.program,
        tail=source_string[epos:],
        pos=epos,
    )
    token_text = source_string[spos:epos]
    token = Token(token_type, prefix, token_text, pos, epos)
    node = analyzer.node_manager.create_node(token, analyzer.previous_node)
    analyzer.node_buffer.append(node)
    analyzer.pos = epos
