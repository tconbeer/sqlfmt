import re

import pytest

from sqlfmt import actions
from sqlfmt.analyzer import Analyzer
from sqlfmt.exception import SqlfmtBracketError, StopJinjaLexing
from sqlfmt.token import Token, TokenType


def test_raise_sqlfmt_bracket_error(default_analyzer: Analyzer) -> None:
    with pytest.raises(SqlfmtBracketError):
        # we need a match, but any match will do.
        s = ")"
        match = re.match(r"(\))", s)
        assert match
        actions.raise_sqlfmt_bracket_error(default_analyzer, "", match)


def test_add_node_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "select a, b, c\n"
    rule = default_analyzer.get_rule("main", "unterm_keyword")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_node_to_buffer(
        default_analyzer, source_string, match, TokenType.UNTERM_KEYWORD
    )

    assert default_analyzer.comment_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 1

    node = default_analyzer.node_buffer[0]
    assert node.is_unterm_keyword

    assert default_analyzer.pos == 6

    rule = default_analyzer.get_rule("main", "name")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_node_to_buffer(default_analyzer, source_string, match, TokenType.NAME)

    assert default_analyzer.comment_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 2

    node = default_analyzer.node_buffer[1]
    assert node.token.type == TokenType.NAME

    assert default_analyzer.pos == 8


def test_safe_add_node_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "end\n"
    rule = default_analyzer.get_rule("main", "statement_end")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    with pytest.raises(SqlfmtBracketError):
        actions.add_node_to_buffer(
            default_analyzer, source_string, match, TokenType.STATEMENT_END
        )
    assert default_analyzer.node_buffer == []
    # does not raise
    actions.safe_add_node_to_buffer(
        default_analyzer, source_string, match, TokenType.STATEMENT_END, TokenType.NAME
    )

    assert default_analyzer.comment_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 1

    node = default_analyzer.node_buffer[0]
    assert node.token.type == TokenType.NAME

    assert default_analyzer.pos == 3


def test_add_comment_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "-- a comment\n"
    rule = default_analyzer.get_rule("main", "comment")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_comment_to_buffer(default_analyzer, source_string, match)

    assert default_analyzer.node_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.comment_buffer) == 1

    comment = default_analyzer.comment_buffer[0]
    assert comment.token.token == source_string.strip()

    assert default_analyzer.pos == 12


def test_handle_newline_with_nodes(default_analyzer: Analyzer) -> None:
    source_string = "a_name\n"
    rule = default_analyzer.get_rule("main", "name")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_node_to_buffer(default_analyzer, source_string, match, TokenType.NAME)
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) > 0
    assert default_analyzer.comment_buffer == []

    rule = default_analyzer.get_rule("main", "newline")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.handle_newline(default_analyzer, source_string, match)
    assert default_analyzer.pos == len(source_string)
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
    assert default_analyzer.pos == 0
    rule = default_analyzer.get_rule("main", "newline")
    for i in range(1, 4):
        match = rule.program.match(source_string, default_analyzer.pos)
        assert match
        actions.handle_newline(default_analyzer, source_string, match)
        assert default_analyzer.pos == i
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

    comment_rule = default_analyzer.get_rule("main", "comment")
    match = comment_rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_comment_to_buffer(default_analyzer, source_string, match)
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.comment_buffer) == 1
    assert default_analyzer.node_buffer == []

    nl_rule = default_analyzer.get_rule("main", "newline")
    match = nl_rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.handle_newline(default_analyzer, source_string, match)
    # do NOT append a line yet
    assert default_analyzer.line_buffer == []
    assert default_analyzer.node_buffer == []
    assert len(default_analyzer.comment_buffer) == 1

    match = nl_rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.handle_newline(default_analyzer, source_string, match)
    # STILL do NOT append a line yet
    assert default_analyzer.line_buffer == []
    assert default_analyzer.node_buffer == []
    assert len(default_analyzer.comment_buffer) == 1

    name_rule = default_analyzer.get_rule("main", "name")
    match = name_rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_node_to_buffer(default_analyzer, source_string, match, TokenType.NAME)
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 1
    assert len(default_analyzer.comment_buffer) == 1

    match = nl_rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.handle_newline(default_analyzer, source_string, match)
    # now we finally create a line
    assert len(default_analyzer.line_buffer) == 1
    assert default_analyzer.node_buffer == []
    assert default_analyzer.comment_buffer == []

    line = default_analyzer.line_buffer[0]
    assert len(line.comments) == 1
    assert len(line.nodes) == 2  # includes nl node


@pytest.mark.parametrize(
    "source_string,has_preceding_star,has_preceding_newline,expected_type",
    [
        (" except", True, False, TokenType.WORD_OPERATOR),
        (" except", True, True, TokenType.WORD_OPERATOR),
        (" except", False, False, TokenType.SET_OPERATOR),
        (" except", False, True, TokenType.SET_OPERATOR),
        (" except all", True, False, TokenType.SET_OPERATOR),  # this is a syntax error
        (" union all", False, False, TokenType.SET_OPERATOR),
    ],
)
def test_handle_set_operator(
    default_analyzer: Analyzer,
    source_string: str,
    has_preceding_star: bool,
    has_preceding_newline: bool,
    expected_type: TokenType,
) -> None:
    rule = default_analyzer.get_rule("main", "set_operator")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match

    if has_preceding_star:
        t = Token(type=TokenType.STAR, prefix="", token="*", spos=0, epos=1)
        n = default_analyzer.node_manager.create_node(t, previous_node=None)
        default_analyzer.node_buffer.append(n)
    elif has_preceding_newline:
        t_nl = Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=0, epos=1)
        n_nl = default_analyzer.node_manager.create_node(t_nl, previous_node=None)
        default_analyzer.node_buffer.append(n_nl)

    if has_preceding_newline and has_preceding_star:
        t_nl = Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=1, epos=2)
        n_nl = default_analyzer.node_manager.create_node(t_nl, previous_node=n)
        default_analyzer.node_buffer.append(n_nl)

    actions.handle_set_operator(default_analyzer, source_string, match)

    node = default_analyzer.node_buffer[-1]
    assert node.token.type == expected_type


@pytest.mark.parametrize(
    "source_string,start_name,end_name",
    [
        (
            "{% config(field='{{this}}') %}",
            "jinja_statement_start",
            "jinja_statement_end",
        ),
        ("{%- set var = that -%}", "jinja_statement_start", "jinja_statement_end"),
        ("{{ simple_var }}", "jinja_expression_start", "jinja_expression_end"),
        ("{{ macro(arg1, arg2) }}", "jinja_expression_start", "jinja_expression_end"),
    ],
)
def test_handle_jinja(
    default_analyzer: Analyzer,
    source_string: str,
    start_name: str,
    end_name: str,
) -> None:
    if "%" in source_string:
        token_type = TokenType.JINJA_STATEMENT
    else:
        token_type = TokenType.JINJA_EXPRESSION
    start_rule = default_analyzer.get_rule("jinja", start_name)
    match = start_rule.program.match(source_string)
    assert match, "Start Rule does not match start of test string"
    with pytest.raises(StopJinjaLexing):
        actions.handle_jinja(
            default_analyzer, source_string, match, start_name, end_name, token_type
        )
    assert len(source_string) == default_analyzer.pos
    assert len(default_analyzer.node_buffer) == 1
    assert default_analyzer.node_buffer[0].token.type == token_type
    assert len(str(default_analyzer.node_buffer[0]).strip()) == len(source_string)


@pytest.mark.parametrize(
    "source_string",
    [
        "{% set my_var %}\n!\n{% endset %}",
        "{% set ns.my_var %}\n!\n{% endset %}",
    ],
)
def test_handle_jinja_set_block(default_analyzer: Analyzer, source_string: str) -> None:
    start_rule = default_analyzer.get_rule("jinja", "jinja_set_block_start")
    match = start_rule.program.match(source_string)
    assert match is not None
    with pytest.raises(StopJinjaLexing):
        actions.handle_jinja_set_block(default_analyzer, source_string, match)
    assert default_analyzer.line_buffer == []
    assert default_analyzer.comment_buffer == []
    assert len(default_analyzer.node_buffer) == 1
    assert default_analyzer.node_buffer[0].token.type == TokenType.DATA


def test_handle_jinja_set_block_unterminated(default_analyzer: Analyzer) -> None:
    source_string = """
    {% set foo %}
    !
    something_else
    """.strip()
    start_rule = default_analyzer.get_rule("jinja", "jinja_set_block_start")
    match = start_rule.program.match(source_string)
    assert match is not None
    with pytest.raises(SqlfmtBracketError) as excinfo:
        actions.handle_jinja_set_block(default_analyzer, source_string, match)

    assert "{% endset %}" in str(excinfo.value)


def test_handle_jinja_if_block(default_analyzer: Analyzer) -> None:
    source_string = """
    {% if foo == bar %}
        column_a,
    {%- elif foo < baz -%}
        column_b,
    {% endif %}
    """.strip()
    start_rule = default_analyzer.get_rule("jinja", "jinja_if_block_start")
    match = start_rule.program.match(source_string)
    assert match is not None
    with pytest.raises(StopJinjaLexing):
        actions.handle_jinja_block(
            default_analyzer,
            source_string,
            match,
            "jinja_if_block_start",
            "jinja_if_block_end",
            ["jinja_elif_block_start", "jinja_else_block_start"],
        )
    assert len(default_analyzer.line_buffer) == 4
    assert (
        default_analyzer.line_buffer[0].nodes[0].token.type
        == TokenType.JINJA_BLOCK_START
    )
    assert (
        default_analyzer.line_buffer[2].nodes[0].token.type
        == TokenType.JINJA_BLOCK_KEYWORD
    )
    assert len(default_analyzer.node_buffer) == 1
    assert default_analyzer.node_buffer[-1].token.type == TokenType.JINJA_BLOCK_END


def test_handle_jinja_if_block_unterminated(default_analyzer: Analyzer) -> None:
    source_string = """
    {% if foo == bar %}
        column_a,
    {%- else -%}
        1+1
    """.strip()
    start_rule = default_analyzer.get_rule("jinja", "jinja_if_block_start")
    match = start_rule.program.match(source_string)
    assert match is not None
    with pytest.raises(SqlfmtBracketError) as excinfo:
        actions.handle_jinja_block(
            default_analyzer,
            source_string,
            match,
            "jinja_if_block_start",
            "jinja_if_block_end",
            ["jinja_elif_block_start", "jinja_else_block_start"],
        )
    assert "{% endif %}" in str(excinfo.value)


def test_handle_jinja_if_block_nested(default_analyzer: Analyzer) -> None:
    source_string = """
    {% if foo == bar %}
        {%- if baz == qux %}
            column_a,
        {% else %}
            column_b,
        {% endif %}
    {%- else -%}
        column_c
    {% endif -%}
    """.strip()
    start_rule = default_analyzer.get_rule("jinja", "jinja_if_block_start")
    match = start_rule.program.match(source_string)
    assert match is not None
    with pytest.raises(StopJinjaLexing):
        actions.handle_jinja_block(
            default_analyzer,
            source_string,
            match,
            "jinja_if_block_start",
            "jinja_if_block_end",
            ["jinja_elif_block_start", "jinja_else_block_start"],
        )
    assert len(default_analyzer.line_buffer) == 8
    assert (
        default_analyzer.line_buffer[0].nodes[0].token.type
        == TokenType.JINJA_BLOCK_START
    )
    assert (
        default_analyzer.line_buffer[1].nodes[0].token.type
        == TokenType.JINJA_BLOCK_START
    )
    assert (
        default_analyzer.line_buffer[3].nodes[0].token.type
        == TokenType.JINJA_BLOCK_KEYWORD
    )
    assert (
        default_analyzer.line_buffer[5].nodes[0].token.type == TokenType.JINJA_BLOCK_END
    )
    assert (
        default_analyzer.line_buffer[6].nodes[0].token.type
        == TokenType.JINJA_BLOCK_KEYWORD
    )
    assert len(default_analyzer.node_buffer) == 1
    assert default_analyzer.node_buffer[-1].token.type == TokenType.JINJA_BLOCK_END


def test_handle_jinja_for_block(default_analyzer: Analyzer) -> None:
    source_string = """
    {% for source in var('marketing_warehouse_ad_group_sources') %}
        {% set relation_source = 'stg_' + source + '_ad_groups' %}

        select
            '{{source}}' as source,
            *
            from {{ ref(relation_source) }}

            {% if not loop.last %}union all{% endif %}
    {% endfor %}
    """.strip()
    start_rule = default_analyzer.get_rule("jinja", "jinja_for_block_start")
    match = start_rule.program.match(source_string)
    assert match is not None, "Did not match starting block"
    with pytest.raises(StopJinjaLexing):
        start_rule.action(default_analyzer, source_string, match)
    assert len(default_analyzer.line_buffer) == 9
    assert (
        default_analyzer.line_buffer[0].nodes[0].token.type
        == TokenType.JINJA_BLOCK_START
    )
    assert (
        default_analyzer.line_buffer[1].nodes[0].token.type == TokenType.JINJA_STATEMENT
    )
    assert len(default_analyzer.node_buffer) == 1
    assert default_analyzer.node_buffer[-1].token.type == TokenType.JINJA_BLOCK_END


def test_handle_unsupported_ddl(default_analyzer: Analyzer) -> None:
    source_string = """
    create table foo (bar int);
    select create, insert from baz;
    create table bar (foo int);
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert len(query.lines) == 3
    first_create_line = query.lines[0]
    assert len(first_create_line.nodes) == 3
    assert first_create_line.nodes[0].token.type == TokenType.DATA
    assert first_create_line.nodes[1].token.type == TokenType.SEMICOLON

    select_line = query.lines[1]
    assert len(select_line.nodes) == 8
    assert select_line.nodes[1].token.type == TokenType.NAME
    assert select_line.nodes[3].token.type == TokenType.NAME


def test_handle_nonreserved_keyword(default_analyzer: Analyzer) -> None:
    source_string = """
    explain select 1;
    select explain, 1 from baz;
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert len(query.lines) == 2
    explain_line = query.lines[0]
    assert len(explain_line.nodes) == 5
    assert explain_line.nodes[0].token.type == TokenType.UNTERM_KEYWORD
    assert explain_line.nodes[1].token.type == TokenType.UNTERM_KEYWORD

    select_line = query.lines[1]
    assert len(select_line.nodes) == 8
    assert select_line.nodes[0].token.type == TokenType.UNTERM_KEYWORD
    assert select_line.nodes[1].token.type == TokenType.NAME
