import re
from typing import TYPE_CHECKING, Callable, List, Optional

from sqlfmt.comment import Comment
from sqlfmt.exception import SqlfmtBracketError, StopRulesetLexing
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
    StopRulesetLexing to revert to SQL lexing
    """
    add_comment_to_buffer(analyzer, source_string, match)
    raise StopRulesetLexing


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
    if first_char in ["+", "-"] and analyzer.previous_node is not None:
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
) -> None:
    """
    Makes a nested call to analyzer.lex, with the new ruleset activated.
    """
    analyzer.push_rules(new_ruleset)
    try:
        analyzer.lex(source_string)
    except StopRulesetLexing:
        analyzer.pop_rules()


def handle_jinja_block_start(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    Lex tags like {% if ... %} and {% for ... %} that open a jinja block
    """
    add_node_to_buffer(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        token_type=TokenType.JINJA_BLOCK_START,
    )
    raise StopRulesetLexing


def handle_jinja_block_keyword(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
) -> None:
    """
    Lex tags like {% elif ... %} and {% else %} that continue an open jinja block
    """
    if analyzer.previous_node is not None:
        try:
            start_tag = analyzer.previous_node.open_jinja_blocks[-1]
        except IndexError:
            # {% if foo %}{% else %} is allowed, but then previous
            # node won't have any open jinja blocks yet.
            # when creating the node, we check to make sure these
            # match
            start_tag = analyzer.previous_node

        previous_node = start_tag.previous_node

        add_node_to_buffer(
            analyzer=analyzer,
            source_string=source_string,
            match=match,
            token_type=TokenType.JINJA_BLOCK_KEYWORD,
            previous_node=previous_node,
            override_analyzer_prev_node=True,
        )
        raise StopRulesetLexing

    else:
        raise_sqlfmt_bracket_error(analyzer, source_string, match)


def handle_jinja_data_block_start(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    new_ruleset: Optional[List[Rule]],
    raises: bool = True,
) -> None:
    """
    Lex tags like {% set foo %} and {% call my_macro %} that open a jinja block
    that can contain arbitrary data.

    This can get called from the JINJA ruleset, in which case we need to
    raise an additional StopRulesetLexing after the JINJA_DATA segment
    is fully lexed.
    """
    add_node_to_buffer(
        analyzer=analyzer,
        source_string=source_string,
        match=match,
        token_type=TokenType.JINJA_BLOCK_START,
    )
    if new_ruleset is None:
        new_ruleset = analyzer.rules
    lex_ruleset(
        analyzer,
        source_string,
        match,
        new_ruleset=new_ruleset,
    )
    if raises:
        raise StopRulesetLexing


def handle_jinja_block_end(
    analyzer: "Analyzer",
    source_string: str,
    match: re.Match,
    reset_sql_depth: bool = False,
) -> None:
    """
    Lex tags like {% endif %} and {% endfor %} that close an open jinja block
    """
    if analyzer.previous_node is not None:
        try:
            start_tag = analyzer.previous_node.open_jinja_blocks[-1]
        except IndexError:
            # {% if foo %}{% else %} is allowed, but then previous
            # node won't have any open jinja blocks yet.
            # when creating the node, we check to make sure these
            # match
            start_tag = analyzer.previous_node

        add_node_to_buffer(
            analyzer=analyzer,
            source_string=source_string,
            match=match,
            token_type=TokenType.JINJA_BLOCK_END,
        )

        if reset_sql_depth:
            analyzer.previous_node.open_brackets = start_tag.open_brackets.copy()

        raise StopRulesetLexing

    else:
        # No open jinja blocks or none that match this token
        raise_sqlfmt_bracket_error(analyzer, source_string=source_string, match=match)


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
    raise StopRulesetLexing


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
