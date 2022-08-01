import pytest

from sqlfmt.exception import SqlfmtBracketError
from sqlfmt.mode import Mode
from sqlfmt.node_manager import NodeManager
from sqlfmt.token import Token, TokenType
from tests.util import read_test_data


@pytest.fixture
def node_manager(default_mode: Mode) -> NodeManager:
    return NodeManager(default_mode.dialect.case_sensitive_names)


def test_calculate_depth(node_manager: NodeManager) -> None:
    select_t = Token(
        type=TokenType.UNTERM_KEYWORD,
        prefix="",
        token="select",
        spos=0,
        epos=6,
    )
    select_n = node_manager.create_node(token=select_t, previous_node=None)
    assert (select_n.depth, select_n.open_brackets) == ((0, 0), [])

    open_paren_t = Token(
        type=TokenType.BRACKET_OPEN,
        prefix="    ",
        token="(",
        spos=8,
        epos=9,
    )
    open_paren_n = node_manager.create_node(token=open_paren_t, previous_node=select_n)
    assert (open_paren_n.depth, open_paren_n.open_brackets) == ((1, 0), [select_n])

    one_t = Token(
        type=TokenType.NUMBER,
        prefix=" ",
        token="1",
        spos=10,
        epos=11,
    )
    one_n = node_manager.create_node(token=one_t, previous_node=open_paren_n)
    assert (one_n.depth, one_n.open_brackets) == ((2, 0), [select_n, open_paren_n])

    close_paren_t = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=11,
        epos=12,
    )
    close_paren_n = node_manager.create_node(token=close_paren_t, previous_node=one_n)
    assert (close_paren_n.depth, close_paren_n.open_brackets) == ((1, 0), [select_n])


def test_calculate_depth_exception(node_manager: NodeManager) -> None:
    close_paren = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=0,
        epos=1,
    )
    with pytest.raises(SqlfmtBracketError):
        _ = node_manager.create_node(close_paren, previous_node=None)


def test_jinja_depth(default_mode: Mode) -> None:
    source_string, _ = read_test_data("unit_tests/test_node/test_jinja_depth.sql")
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    expected = [
        (0, 0),  # {{ config(materialized="table") }}
        (0, 0),  # \n
        (0, 0),  # \n
        (0, 0),  # {%- set n = 5 -%}
        (0, 0),  # \n
        (0, 0),  # with
        (1, 0),  # \n
        (1, 0),  # {% for i in range(n) %}
        (1, 1),  # \n
        (1, 1),  # dont_do_this_
        (1, 1),  # {{ i }}
        (1, 1),  # as
        (1, 1),  # (
        (2, 1),  # \n
        (2, 1),  # {% if foo %}
        (2, 2),  # \n
        (2, 2),  # select
        (3, 2),  # \n
        (2, 1),  # {% elif bar %}
        (2, 2),  # \n
        (2, 2),  # select distinct
        (3, 2),  # \n
        (2, 1),  # {% elif baz %}
        (2, 2),  # \n
        (2, 2),  # select top 25
        (3, 2),  # \n
        (2, 1),  # {% else %}
        (2, 2),  # \n
        (2, 2),  # select
        (3, 2),  # \n
        (3, 1),  # {% endif %}
        (3, 1),  # \n
        (3, 1),  # my_col
        (3, 1),  # \n
        (2, 1),  # from
        (3, 1),  # \n
        (3, 1),  # {% if i == qux %}
        (3, 2),  # \n
        (3, 2),  # zip
        (3, 2),  # \n
        (3, 1),  # {% else %}
        (3, 2),  # \n
        (3, 2),  # zap
        (3, 2),  # \n
        (3, 1),  # {% endif %}
        (3, 1),  # \n
        (1, 1),  # )
        (1, 1),  # {% if not loop.last %}
        (1, 2),  # ,
        (1, 1),  # {% endif%}
        (1, 1),  # \n
        (1, 0),  # {% endfor %}
        (1, 0),  # \n
        (1, 0),  # {% for i in range(n) %}
        (1, 1),  # \n
        (0, 1),  # select
        (1, 1),  # \n
        (1, 1),  # *
        (1, 1),  # \n
        (0, 1),  # from
        (1, 1),  # \n
        (1, 1),  # dont_do_this_
        (1, 1),  # {{ i }}
        (1, 1),  # \n
        (1, 1),  # {% if not loop.last -%}
        (1, 2),  # \n
        (0, 2),  # union all
        (0, 2),  # \n
        (0, 1),  # {%- endif %}
        (0, 1),  # \n
        (0, 0),  # {% endfor %}
        (0, 0),  # \n
    ]
    actual = [node.depth for node in q.nodes]
    assert actual == expected


def test_create_node_raises_bracket_error_on_jinja_block_end(
    node_manager: NodeManager,
) -> None:
    t = Token(
        type=TokenType.JINJA_BLOCK_END,
        prefix="",
        token="{% endif %}",
        spos=0,
        epos=11,
    )
    with pytest.raises(SqlfmtBracketError):
        _ = node_manager.create_node(t, previous_node=None)


def test_union_depth(default_mode: Mode) -> None:
    source_string, _ = read_test_data("unit_tests/test_node/test_union_depth.sql")
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)

    expected = [
        (0, 0),  # select,
        (1, 0),  # 1,
        (1, 0),  # \n,
        (1, 0),  # \n,
        (0, 0),  # union,
        (0, 0),  # \n,
        (0, 0),  # \n,
        (0, 0),  # select,
        (1, 0),  # 2,
        (1, 0),  # \n,
        (1, 0),  # \n,
        (0, 0),  # union all,
        (0, 0),  # \n,
        (0, 0),  # \n,
        (0, 0),  # (,
        (1, 0),  # \n,
        (1, 0),  # select,
        (2, 0),  # 3,
        (2, 0),  # \n,
        (0, 0),  # ),
        (0, 0),  # \n'
    ]
    actual_depth = [n.depth for n in q.nodes]
    assert actual_depth == expected


def test_capitalization(default_mode: Mode) -> None:
    source_string = (
        "SELECT A, B, \"C\", {{ D }}, e, 'f', 'G'\n" 'fROM "H"."j" Join I ON k And L\n'
    )
    expected = (
        "select a, b, \"C\", {{ D }}, e, 'f', 'G'\n" 'from "H"."j" join i on k and l\n'
    )
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert parsed_string == expected


@pytest.mark.parametrize(
    "source_string,expected",
    [
        (
            "SELECT A, B, \"C\", {{ D }}, e, 'f', 'G'\n"
            'fROM "H"."j" Join I ON k And L\n',
            "select A, B, \"C\", {{ D }}, e, 'f', 'G'\n"
            'from "H"."j" join I on k and L\n',
        ),
        (
            "SELECT toString(1) AS Test_string, toDateTime64('2022-05-25', 3) "
            "AS Test_dateTime64, ifNull(null, 'TestNull') as testIf, "
            "JSONExtractString('{\"abc\": \"hello\"}', 'abc') as testJSON\n",
            "select toString(1) as Test_string, toDateTime64('2022-05-25', 3) "
            "as Test_dateTime64, ifNull(null, 'TestNull') as testIf, "
            "JSONExtractString('{\"abc\": \"hello\"}', 'abc') as testJSON\n",
        ),
    ],
)
def test_capitalization_clickhouse(
    source_string: str, expected: str, clickhouse_mode: Mode
) -> None:
    q = clickhouse_mode.dialect.initialize_analyzer(
        line_length=clickhouse_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert parsed_string == expected


@pytest.mark.parametrize(
    "source_string",
    [
        "OVER",
        "IN",
        "AND",
        "EXCEPT",
        "REPLACE",
        "UNION",
        "SUM",
        "BETWEEN",
    ],
)
def test_capitalization_operators(default_mode: Mode, source_string: str) -> None:
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert parsed_string.rstrip("\n") == source_string.lower()


@pytest.mark.parametrize(
    "source_string",
    [
        "my_schema.my_table\n",
        "my_table.*\n",
        '"my_table".*\n',
        "{{ my_schema }}.my_table\n",
        "my_schema.{{ my_table }}\n",
        "my_database.my_schema.my_table\n",
        'my_schema."my_table"\n',
        '"my_schema".my_table\n',
        '"my_schema"."my_table"\n',
        "my_table.$2\n",
        '"my_table".$2\n',
        "my_schema.{% if foo %}bar{% else %}baz{% endif %}\n",
        "json_field:key_name\n",
        'json:"KeyName"\n',
        "my_table.json_field:key_name\n",
        '"JSONField":"KeyName"::varchar\n',
        '"JSONField":"KeyName"::varchar\n',
        "my_array[1]\n",
        "my_array[1:2]\n",
        '"my_array"[1]\n',
        '"my_array"[1:2]\n',
    ],
)
def test_identifier_whitespace(default_mode: Mode, source_string: str) -> None:
    """
    Ensure we do not inject spaces into qualified identifier names
    """
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert source_string == parsed_string


@pytest.mark.parametrize(
    "source_string",
    [
        "(my_schema.my_table)\n",
        "count(*)\n",
        "count(*) over ()\n",
        "something in (somthing_else)\n",
        "some_array[offset(0)]\n",
        "some_array_func(args)[offset(0)]\n",
        "(())\n",
        "([])\n",
        "()[] + foo()[offset(1)]\n",
    ],
)
def test_bracket_whitespace(default_mode: Mode, source_string: str) -> None:
    q = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    ).parse_query(source_string=source_string)
    parsed_string = "".join(str(line) for line in q.lines)
    assert source_string == parsed_string
