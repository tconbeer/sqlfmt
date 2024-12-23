import re

import pytest
from sqlfmt import actions
from sqlfmt.analyzer import Analyzer
from sqlfmt.exception import SqlfmtBracketError, StopRulesetLexing
from sqlfmt.rules import FUNCTION, JINJA
from sqlfmt.token import Token, TokenType

from tests.util import read_test_data


@pytest.fixture
def jinja_analyzer(default_analyzer: Analyzer) -> Analyzer:
    default_analyzer.push_rules(JINJA)
    return default_analyzer


@pytest.fixture
def function_analyzer(default_analyzer: Analyzer) -> Analyzer:
    default_analyzer.push_rules(FUNCTION)
    return default_analyzer


def test_raise_sqlfmt_bracket_error(default_analyzer: Analyzer) -> None:
    with pytest.raises(SqlfmtBracketError):
        # we need a match, but any match will do.
        s = ")"
        match = re.match(r"(\))", s)
        assert match
        actions.raise_sqlfmt_bracket_error(default_analyzer, "", match)


def test_add_node_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "select a, b, c\n"
    rule = default_analyzer.get_rule("unterm_keyword")
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

    rule = default_analyzer.get_rule("name")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_node_to_buffer(default_analyzer, source_string, match, TokenType.NAME)

    assert default_analyzer.comment_buffer == []
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) == 2

    node = default_analyzer.node_buffer[1]
    assert node.token.type is TokenType.NAME

    assert default_analyzer.pos == 8


def test_safe_add_node_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "end\n"
    rule = default_analyzer.get_rule("statement_end")
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
    assert node.token.type is TokenType.NAME

    assert default_analyzer.pos == 3


def test_add_comment_to_buffer(default_analyzer: Analyzer) -> None:
    source_string = "-- a comment\n"
    rule = default_analyzer.get_rule("comment")
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
    rule = default_analyzer.get_rule("name")
    match = rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_node_to_buffer(default_analyzer, source_string, match, TokenType.NAME)
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.node_buffer) > 0
    assert default_analyzer.comment_buffer == []

    rule = default_analyzer.get_rule("newline")
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
    rule = default_analyzer.get_rule("newline")
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

    comment_rule = default_analyzer.get_rule("comment")
    match = comment_rule.program.match(source_string, pos=default_analyzer.pos)
    assert match
    actions.add_comment_to_buffer(default_analyzer, source_string, match)
    assert default_analyzer.line_buffer == []
    assert len(default_analyzer.comment_buffer) == 1
    assert default_analyzer.node_buffer == []

    nl_rule = default_analyzer.get_rule("newline")
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

    name_rule = default_analyzer.get_rule("name")
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
    rule = default_analyzer.get_rule("set_operator")
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
    jinja_analyzer: Analyzer,
    source_string: str,
    start_name: str,
    end_name: str,
) -> None:
    if "%" in source_string:
        token_type = TokenType.JINJA_STATEMENT
    else:
        token_type = TokenType.JINJA_EXPRESSION
    start_rule = jinja_analyzer.get_rule(start_name)
    match = start_rule.program.match(source_string)
    assert match, "Start Rule does not match start of test string"
    with pytest.raises(StopRulesetLexing):
        actions.handle_jinja(
            jinja_analyzer, source_string, match, start_name, end_name, token_type
        )
    assert len(source_string) == jinja_analyzer.pos
    assert len(jinja_analyzer.node_buffer) == 1
    assert jinja_analyzer.node_buffer[0].token.type == token_type
    assert len(str(jinja_analyzer.node_buffer[0]).strip()) == len(source_string)


@pytest.mark.parametrize(
    "source_string",
    [
        "{% set my_var %}\n!\n{% endset %}",
        "{% set ns.my_var %}\n!\n{% endset %}",
    ],
)
def test_handle_jinja_set_block(default_analyzer: Analyzer, source_string: str) -> None:
    query = default_analyzer.parse_query(source_string=source_string)
    assert len(query.lines) == 3
    assert query.lines[0].nodes[0].token.type == TokenType.JINJA_BLOCK_START
    assert query.lines[1].nodes[0].token.type == TokenType.DATA
    assert query.lines[2].nodes[0].token.type == TokenType.JINJA_BLOCK_END


def test_handle_jinja_set_block_nested(default_analyzer: Analyzer) -> None:
    source_string = """
    {% set foo %}
    !
    something_else
    {% set bar %}bar{% endset %}
    {{ bar }}
    {% set baz %}
    baz
    {% endset %}
    {{ baz ~ bar }}
    {% endset %}
    """.strip()
    q = default_analyzer.parse_query(source_string=source_string)
    assert q.lines[0].nodes[0].token.type == TokenType.JINJA_BLOCK_START
    assert q.lines[1].nodes[0].token.type == TokenType.DATA
    assert q.lines[2].nodes[0].token.type == TokenType.JINJA_BLOCK_START
    assert q.lines[2].nodes[1].token.type == TokenType.DATA
    assert len(q.lines[2].nodes[1].open_jinja_blocks) == 2
    assert q.lines[2].nodes[2].token.type == TokenType.JINJA_BLOCK_END
    assert q.lines[3].nodes[0].token.type == TokenType.DATA
    assert q.lines[4].nodes[0].token.type == TokenType.JINJA_BLOCK_START
    assert q.lines[5].nodes[0].token.type == TokenType.DATA
    assert q.lines[6].nodes[0].token.type == TokenType.JINJA_BLOCK_END
    assert q.lines[7].nodes[0].token.type == TokenType.DATA
    assert q.lines[8].nodes[0].token.type == TokenType.JINJA_BLOCK_END


def test_handle_jinja_if_block(default_analyzer: Analyzer) -> None:
    source_string = """
    {% if foo == bar %}
        column_a,
    {%- elif foo < baz -%}
        column_b,
    {% endif %}
    """.strip()
    query = default_analyzer.parse_query(source_string=source_string)
    assert len(query.lines) == 5
    assert query.lines[0].nodes[0].token.type is TokenType.JINJA_BLOCK_START
    assert query.lines[2].nodes[0].token.type is TokenType.JINJA_BLOCK_KEYWORD
    assert query.lines[-1].nodes[0].token.type is TokenType.JINJA_BLOCK_END


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
    query = default_analyzer.parse_query(source_string=source_string)
    assert len(query.lines) == 9
    assert query.lines[0].nodes[0].token.type is TokenType.JINJA_BLOCK_START
    assert query.lines[1].nodes[0].token.type is TokenType.JINJA_BLOCK_START
    assert query.lines[3].nodes[0].token.type is TokenType.JINJA_BLOCK_KEYWORD
    assert query.lines[3].nodes[0].previous_node == query.lines[0].nodes[-1]
    assert query.lines[5].nodes[0].token.type is TokenType.JINJA_BLOCK_END
    assert query.lines[6].nodes[0].token.type is TokenType.JINJA_BLOCK_KEYWORD
    assert query.lines[6].nodes[0].previous_node is None
    assert query.lines[-1].nodes[0].token.type is TokenType.JINJA_BLOCK_END


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
    query = default_analyzer.parse_query(source_string=source_string)
    assert len(query.lines) == 10
    start_node = query.nodes[0]
    assert start_node.token.type is TokenType.JINJA_BLOCK_START
    assert query.nodes[1].open_jinja_blocks == [start_node]
    assert query.nodes[-2].token.type is TokenType.JINJA_BLOCK_END


@pytest.mark.parametrize(
    "source_string",
    [
        "{% endfor %}",
        "{% if foo %}{% endfor %}",
        "{% for foo in bar %}{% endif %}",
        "{% else %}",
    ],
)
def test_handle_jinja_end_block_raises(
    default_analyzer: Analyzer, source_string: str
) -> None:
    with pytest.raises(SqlfmtBracketError):
        _ = default_analyzer.parse_query(source_string=source_string)


@pytest.mark.parametrize(
    "source_string",
    [
        "{% for foo in bar %} {% endfor %}",
        "{% if foo %}{% endif %}",
        "{% if foo %} {% else %}{% endif %}",
        "{% set foo %}{% endset %}",
        "{% call noop_statement('main', status_string) %}{% endcall %}",
    ],
)
def test_handle_jinja_empty_blocks(
    default_analyzer: Analyzer, source_string: str
) -> None:
    q = default_analyzer.parse_query(source_string=source_string)
    assert len(q.lines) == 1
    assert q.nodes[0].token.type is TokenType.JINJA_BLOCK_START
    assert q.nodes[-2].token.type is TokenType.JINJA_BLOCK_END


def test_handle_jinja_call_statement_block(default_analyzer: Analyzer) -> None:
    source_string = """
    select 1,
    {% call statement() %}
    select 2 from foo
    {% endcall %}
    2
    """.strip()
    query = default_analyzer.parse_query(source_string=source_string.lstrip())

    assert query.lines[1].nodes[0].token.type is TokenType.JINJA_BLOCK_START
    assert query.lines[-2].nodes[0].token.type is TokenType.JINJA_BLOCK_END

    # ensure endcall block resets sql depth
    outer_select = query.nodes[0]
    assert query.nodes[-1].depth == (1, 0)
    assert query.nodes[-1].open_brackets == [outer_select]


def test_handle_jinja_call_block(default_analyzer: Analyzer) -> None:
    source_string = """
    select 1,
    {% call dbt_unit_testing.mock_ref('foo') %}
    a | b
    foo | bar
    {% endcall %}
    2
    """.strip()
    query = default_analyzer.parse_query(source_string=source_string.lstrip())

    assert query.lines[1].nodes[0].token.type is TokenType.JINJA_BLOCK_START
    assert query.lines[1].nodes[1].token.type is TokenType.NEWLINE
    assert query.lines[2].nodes[0].token.type is TokenType.DATA
    assert query.lines[3].nodes[0].token.type is TokenType.JINJA_BLOCK_END
    assert query.lines[4].nodes[0].token.type is TokenType.NUMBER

    # ensure call block does not change sql depth
    outer_select = query.nodes[0]
    assert query.nodes[-1].depth == (1, 0)
    assert query.nodes[-1].open_brackets == [outer_select]


def test_handle_unsupported_ddl(default_analyzer: Analyzer) -> None:
    source_string = """
    create table foo (bar int);
    select create, insert from baz;
    create table bar (foo int);
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert len(query.lines) == 3
    first_create_line = query.lines[0]
    assert len(first_create_line.nodes) == 3  # data, semicolon, newline
    assert first_create_line.nodes[0].token.type is TokenType.DATA
    assert first_create_line.nodes[-2].token.type is TokenType.SEMICOLON

    select_line = query.lines[1]
    assert len(select_line.nodes) == 8
    assert select_line.nodes[1].token.type is TokenType.NAME
    assert select_line.nodes[3].token.type is TokenType.NAME


def test_handle_explain(default_analyzer: Analyzer) -> None:
    source_string = """
    explain select 1;
    select explain, 1 from baz;
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert len(query.lines) == 2
    explain_line = query.lines[0]
    assert len(explain_line.nodes) == 5
    assert explain_line.nodes[0].token.type is TokenType.UNTERM_KEYWORD
    assert explain_line.nodes[1].token.type is TokenType.UNTERM_KEYWORD

    select_line = query.lines[1]
    assert len(select_line.nodes) == 8
    assert select_line.nodes[0].token.type is TokenType.UNTERM_KEYWORD
    assert select_line.nodes[1].token.type is TokenType.NAME


def test_handle_semicolon(default_analyzer: Analyzer) -> None:
    source_string = """
    select 1;
    create function foo() as select 1;
    select 1;
    create function foo() as $$ select 1 $$;
    select 1;
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert len(query.lines) == 5
    for line in query.lines:
        assert line.nodes[0].is_unterm_keyword


def test_handle_ddl_as_unquoted(function_analyzer: Analyzer) -> None:
    source_string = """
    create function foo
    language sql
    as select
    """
    function_analyzer.lex(source_string=source_string.lstrip())
    assert len(function_analyzer.node_buffer) == 2
    assert function_analyzer.node_buffer[0].is_unterm_keyword
    # ensure we're lexing using the main ruleset (implying an empty rule stack)
    assert function_analyzer.node_buffer[1].is_unterm_keyword
    assert not function_analyzer.rule_stack


def test_handle_ddl_as_quoted(function_analyzer: Analyzer) -> None:
    source_string = """
    create function foo
    language sql
    as $$select
    1$$ security definer
    """
    function_analyzer.lex(source_string=source_string.lstrip())
    assert len(function_analyzer.node_buffer) == 3
    assert function_analyzer.node_buffer[0].is_unterm_keyword
    # ensure we're lexing using the create_fn rules (implying an empty rule stack)
    assert function_analyzer.node_buffer[1].token.type is TokenType.QUOTED_NAME
    assert function_analyzer.rule_stack
    # ensure security definer is being lexed with the create_function ruleset (as a kw)
    assert function_analyzer.node_buffer[2].is_unterm_keyword


def test_handle_closing_angle_bracket(default_analyzer: Analyzer) -> None:
    source_string = """
    table<a int, b int>,
    array<struct<a int, b string>>,
    x >> 2,
    yr > 2022,
    foo >>= 'bar',
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert all([line.depth == (0, 0) for line in query.lines])
    table_line = query.lines[0]
    assert table_line.nodes[0].is_opening_bracket
    assert table_line.nodes[-3].is_closing_bracket
    array_line = query.lines[1]
    assert array_line.nodes[0].is_opening_bracket
    assert array_line.nodes[-3].is_closing_bracket
    assert array_line.nodes[-4].is_closing_bracket
    assert all([line.nodes[1].is_operator for line in query.lines[2:]])


def test_handle_number_unary(default_analyzer: Analyzer) -> None:
    source_string = """
    select
        +1,
        -2,
        -1 + -2,
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    numbers = [str(n).strip() for n in query.nodes if n.token.type is TokenType.NUMBER]
    assert numbers == ["+1", "-2", "-1", "-2"]


def test_handle_number_binary(default_analyzer: Analyzer) -> None:
    source_string = """
    select
        1 +1,
        1 -1,
        -1+2,
        something-2,
        (something)+2,
        case when true then foo else bar end+2
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    numbers = [str(n).strip() for n in query.nodes if n.token.type is TokenType.NUMBER]
    assert numbers == ["1", "1", "1", "1", "-1", "2", "2", "2", "2"]


def test_handle_nested_dictionary_in_jinja_expression(
    jinja_analyzer: Analyzer,
) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_actions/test_handle_potentially_nested_tokens.sql"
    )
    match = re.match(r"(\{\{)", source_string)
    assert match
    actions.handle_potentially_nested_tokens(
        analyzer=jinja_analyzer,
        source_string=source_string,
        match=match,
        start_name="jinja_expression_start",
        end_name="jinja_expression_end",
        token_type=TokenType.JINJA_EXPRESSION,
    )
    assert jinja_analyzer.pos == 355


def test_handle_reserved_keywords(default_analyzer: Analyzer) -> None:
    source_string = """
    select case;
    select foo.case;
    select foo.select;
    interval;
    foo.interval;
    explain;
    foo.explain;
    """
    query = default_analyzer.parse_query(source_string=source_string.lstrip())
    assert len(query.lines) == 7
    case_line = query.lines[0]
    assert len(case_line.nodes) == 4
    assert case_line.nodes[0].token.type is TokenType.UNTERM_KEYWORD
    assert case_line.nodes[1].token.type is TokenType.STATEMENT_START

    case_name_line = query.lines[1]
    assert len(case_name_line.nodes) == 6
    assert case_name_line.nodes[0].token.type is TokenType.UNTERM_KEYWORD
    assert case_name_line.nodes[1].token.type is TokenType.NAME
    assert case_name_line.nodes[2].token.type is TokenType.DOT
    assert case_name_line.nodes[3].token.type is TokenType.NAME

    select_name_line = query.lines[2]
    assert len(select_name_line.nodes) == 6
    assert select_name_line.nodes[0].token.type is TokenType.UNTERM_KEYWORD
    assert select_name_line.nodes[1].token.type is TokenType.NAME
    assert select_name_line.nodes[2].token.type is TokenType.DOT
    assert select_name_line.nodes[3].token.type is TokenType.NAME

    interval_line = query.lines[3]
    assert len(interval_line.nodes) == 3
    assert interval_line.nodes[0].token.type is TokenType.WORD_OPERATOR

    interval_name_line = query.lines[4]
    assert len(interval_name_line.nodes) == 5
    assert interval_name_line.nodes[0].token.type is TokenType.NAME
    assert interval_name_line.nodes[1].token.type is TokenType.DOT
    assert interval_name_line.nodes[2].token.type is TokenType.NAME

    explain_line = query.lines[5]
    assert len(explain_line.nodes) == 3
    assert explain_line.nodes[0].token.type is TokenType.UNTERM_KEYWORD

    explain_name_line = query.lines[6]
    assert len(explain_name_line.nodes) == 5
    assert explain_name_line.nodes[0].token.type is TokenType.NAME
    assert explain_name_line.nodes[1].token.type is TokenType.DOT
    assert explain_name_line.nodes[2].token.type is TokenType.NAME
