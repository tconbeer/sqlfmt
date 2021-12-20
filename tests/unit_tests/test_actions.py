import re

import pytest

from sqlfmt import actions
from sqlfmt.analyzer import Analyzer
from sqlfmt.exception import SqlfmtMultilineError
from sqlfmt.token import TokenType


def test_raise_sqlfmt_multiline_error(default_analyzer: Analyzer) -> None:
    with pytest.raises(SqlfmtMultilineError):
        s = ")"
        match = re.match(r"(\))", s)
        assert match
        actions.raise_sqlfmt_multiline_error(default_analyzer, "", match)


def test_add_node_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "select a, b, c\n"
    match = re.match(r"(select)", source_string)
    assert match
    pos = actions.add_node_to_buffer(
        default_analyzer, source_string, match, TokenType.UNTERM_KEYWORD
    )

    assert default_analyzer.comment_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 1

    node = default_analyzer.node_buffer[0]
    assert node.is_unterm_keyword

    assert pos == 6

    match = re.match(r"\s*(\w+)", source_string[pos:])
    assert match
    pos = pos + actions.add_node_to_buffer(
        default_analyzer, source_string[pos:], match, TokenType.NAME
    )

    assert default_analyzer.comment_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 2

    node = default_analyzer.node_buffer[1]
    assert node.token.type == TokenType.NAME

    assert pos == 8


def test_add_comment_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "-- a comment\n"
    match = re.match(r"(--[^\n]*)", source_string)
    assert match
    pos = actions.add_comment_to_buffer(default_analyzer, source_string, match)

    assert default_analyzer.node_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.comment_buffer) == 1

    comment = default_analyzer.comment_buffer[0]
    assert comment.token.token == source_string.strip()

    assert pos == 12


def test_handle_newline_with_nodes(default_analyzer: Analyzer) -> None:
    source_string = "a_name\n"
    match = re.match(r"(\w+)", source_string)
    assert match
    pos = actions.add_node_to_buffer(
        default_analyzer, source_string, match, TokenType.NAME
    )
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) > 0
    assert default_analyzer.comment_buffer == []

    match = re.match(r"(\n)", source_string[pos:])
    assert match
    pos = pos + actions.handle_newline(default_analyzer, source_string[pos:], match)
    assert pos == len(source_string)
    assert len(default_analyzer.line_buffer) == 1
    assert default_analyzer.node_buffer == []
    assert default_analyzer.comment_buffer == []
    line = default_analyzer.line_buffer[0]
    assert str(line) == "a_name\n"


def test_handle_newline_empty(default_analyzer: Analyzer) -> None:
    source_string = "\n\n\n"
    assert default_analyzer.line_buffer == []
    assert default_analyzer.comment_buffer == []
    assert default_analyzer.node_buffer == []
    pos = 0
    for i in range(1, 4):
        match = re.match(r"(\n)", source_string[pos:])
        assert match
        pos = pos + actions.handle_newline(default_analyzer, source_string[pos:], match)
        assert pos == i
        assert len(default_analyzer.line_buffer) == i
        assert default_analyzer.node_buffer == []
        assert default_analyzer.comment_buffer == []
        line = default_analyzer.line_buffer[i - 1]
        assert str(line) == "\n"


def test_handle_newline_leading_comments(default_analyzer: Analyzer) -> None:
    source_string = "-- a comment\n\nsomething\n"
    assert default_analyzer.line_buffer == []
    assert default_analyzer.comment_buffer == []
    assert default_analyzer.node_buffer == []

    pos = 0
    match = re.match(r"(--[^\n]*)", source_string[pos:])
    assert match
    pos = pos + actions.add_comment_to_buffer(
        default_analyzer, source_string[pos:], match
    )
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.comment_buffer) == 1
    assert default_analyzer.node_buffer == []

    match = re.match(r"(\n)", source_string[pos:])
    assert match
    pos = pos + actions.handle_newline(default_analyzer, source_string[pos:], match)
    # do NOT append a line yet
    assert default_analyzer.line_buffer == []
    assert default_analyzer.node_buffer == []
    assert len(default_analyzer.comment_buffer) == 1

    match = re.match(r"(\n)", source_string[pos:])
    assert match
    pos = pos + actions.handle_newline(default_analyzer, source_string[pos:], match)
    # do NOT append a line yet
    assert default_analyzer.line_buffer == []
    assert default_analyzer.node_buffer == []
    assert len(default_analyzer.comment_buffer) == 1

    match = re.match(r"(\w+)", source_string[pos:])
    assert match
    pos = pos + actions.add_node_to_buffer(
        default_analyzer, source_string[pos:], match, TokenType.NAME
    )
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 1
    assert len(default_analyzer.comment_buffer) == 1

    match = re.match(r"(\n)", source_string[pos:])
    assert match
    pos = pos + actions.handle_newline(default_analyzer, source_string[pos:], match)
    # now we finally create a line
    assert len(default_analyzer.line_buffer) == 1
    assert default_analyzer.node_buffer == []
    assert default_analyzer.comment_buffer == []

    line = default_analyzer.line_buffer[0]
    assert len(line.comments) == 1
    assert len(line.nodes) == 2  # includes nl node


@pytest.mark.parametrize(
    "source_string,pattern,rule_name,attribute",
    [
        ("{% config(field='{{this}}') %}", r"(\{%)", "jinja_start", "node_buffer"),
        ("/* outer /* nested */ outer */", r"(/\*)", "comment_start", "comment_buffer"),
    ],
)
def test_handle_complex_token_nested(
    default_analyzer: Analyzer,
    source_string: str,
    pattern: str,
    rule_name: str,
    attribute: str,
) -> None:
    match = re.match(pattern, source_string)
    assert match, "poorly formed test"
    pos = actions.handle_complex_tokens(
        default_analyzer, source_string, match, rule_name
    )
    assert len(source_string) == pos
    buf = getattr(default_analyzer, attribute)
    assert len(buf) == 1
    assert len(str(buf[0]).strip()) == len(source_string)
