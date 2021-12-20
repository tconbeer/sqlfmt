import re

from sqlfmt.analyzer import MAYBE_WHITESPACES, Analyzer, Rule, group
from sqlfmt.exception import SqlfmtBracketError, SqlfmtMultilineError
from sqlfmt.line import Comment, Line, Node
from sqlfmt.token import Token, TokenType


def raise_sqlfmt_multiline_error(
    _: Analyzer, source_string: str, match: re.Match
) -> int:
    spos, epos = match.span(1)
    raw_token = source_string[spos:epos]
    raise SqlfmtMultilineError(
        f"Encountered closing bracket '{raw_token}' at position"
        f" {spos}, before matching opening bracket:"
        f" {source_string[spos:spos+50]}"
    )


def add_node_to_buffer(
    analyzer: Analyzer,
    source_string: str,
    match: re.Match,
    token_type: TokenType,
) -> int:
    """
    Create a token of token_type from the match, then create a Node
    from that token and append it to the Analyzer's buffer
    """
    token = Token.from_match(source_string, match, token_type)
    node = Node.from_token(token=token, previous_node=analyzer.previous_node)
    analyzer.node_buffer.append(node)
    return token.epos


def safe_add_node_to_buffer(
    analyzer: Analyzer,
    source_string: str,
    match: re.Match,
    token_type: TokenType,
    fallback_token_type: TokenType,
) -> int:
    """
    Try to create a token of token_type from the match; if that fails
    with a SqlfmtBracketError, create a token of fallback_token_type.
    Then create a Node from that token and append it to the Analyzer's buffer
    """
    try:
        token = Token.from_match(source_string, match, token_type)
        node = Node.from_token(token=token, previous_node=analyzer.previous_node)
    except SqlfmtBracketError:
        token = Token.from_match(source_string, match, fallback_token_type)
        node = Node.from_token(token=token, previous_node=analyzer.previous_node)
    finally:
        analyzer.node_buffer.append(node)
        return token.epos


def add_comment_to_buffer(
    analyzer: Analyzer,
    source_string: str,
    match: re.Match,
) -> int:
    """
    Create a token of token_type from the match, then create a Comment
    from that token and append it to the Analyzer's buffer
    """
    token = Token.from_match(source_string, match, TokenType.COMMENT)
    is_standalone = (not bool(analyzer.node_buffer)) or "\n" in token.token
    comment = Comment(token=token, is_standalone=is_standalone)
    analyzer.comment_buffer.append(comment)
    return token.epos


def handle_newline(
    analyzer: Analyzer,
    source_string: str,
    match: re.Match,
) -> int:
    """
    When a newline is encountered in the source, we typically want to create a
    new line in the Analyzer's line_buffer, flushing the node_buffer and
    comment_buffer in the process.

    However, if we have lexed a standalone comment, we do not want to create
    a Line with only that comment; instead, it must be added to the next Line
    that contains Nodes
    """
    nl_token = Token.from_match(source_string, match, TokenType.NEWLINE)
    nl_node = Node.from_token(token=nl_token, previous_node=analyzer.previous_node)
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
    return nl_token.epos


def handle_complex_tokens(
    analyzer: Analyzer,
    source_string: str,
    match: re.Match,
    rule_name: str,
) -> int:
    """
    Polyglot tries to match multiline jinja tags and comments in one go,
    however, due to nesting, this isn't always possible. This Action
    recursively searches for the terminating token, then appends the entire
    token to the Analyzer's buffer
    """
    # extract properties from matching start of token
    pos, _ = match.span(0)
    spos, epos = match.span(1)
    prefix = source_string[pos:spos]
    # compile a new pattern to match either the ending
    # pattern or a nesting pattern
    start_rule: Rule = list(
        filter(lambda rule: rule.name == rule_name, analyzer.rules)
    )[0]
    terminations = {
        "jinja_start": "jinja_end",
        "comment_start": "comment_end",
    }
    end_rule: Rule = list(
        filter(lambda rule: rule.name == terminations[rule_name], analyzer.rules)
    )[0]
    patterns = [start_rule.pattern, end_rule.pattern]
    program = re.compile(
        MAYBE_WHITESPACES + group(*patterns), re.IGNORECASE | re.DOTALL
    )
    # search for the ending token, and/or nest levels deeper
    epos = analyzer.search_for_terminating_token(
        start_rule=rule_name,
        program=program,
        nesting_program=start_rule.program,
        tail=source_string[epos:],
        pos=epos,
    )
    token = source_string[spos:epos]
    if start_rule.name == "jinja_start":
        token_type = TokenType.JINJA
        new_token = Token(token_type, prefix, token, pos, epos)
        node = Node.from_token(new_token, analyzer.previous_node)
        analyzer.node_buffer.append(node)
    else:
        token_type = TokenType.COMMENT
        new_token = Token(token_type, prefix, token, pos, epos)
        is_standalone = (not bool(analyzer.node_buffer)) or "\n" in new_token.token
        comment = Comment(token=new_token, is_standalone=is_standalone)
        analyzer.comment_buffer.append(comment)
    return epos
