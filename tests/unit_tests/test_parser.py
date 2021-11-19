import pytest

from sqlfmt.dialect import SqlfmtParsingError
from sqlfmt.mode import Mode
from sqlfmt.parser import Node, Query, SqlfmtMultilineError
from sqlfmt.token import Token, TokenType
from tests.util import read_test_data


def test_calculate_depth() -> None:
    t = Token(
        type=TokenType.UNTERM_KEYWORD,
        prefix="",
        token="select",
        spos=0,
        epos=6,
    )
    res = Node.calculate_depth(t, inherited_depth=0, open_brackets=[])

    assert res == (0, 1, [t])

    t = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=0,
        epos=0,
    )

    b = Token(
        type=TokenType.BRACKET_OPEN,
        prefix="    ",
        token="(",
        spos=0,
        epos=0,
    )

    res = Node.calculate_depth(t, inherited_depth=2, open_brackets=[b])

    assert res == (1, 0, [])


def test_simple_query_parsing(all_output_modes: Mode) -> None:

    source_string, _ = read_test_data(
        "unit_tests/test_parser/test_simple_query_parsing.sql"
    )

    q = Query.from_source(source_string=source_string, mode=all_output_modes)

    assert q
    assert q.source_string == source_string
    # assert len(q.lines) == 6

    # expected_line_depths = [0, 1, 1, 1, 0, 0]

    # computed_line_depths = [line.depth for line in q.lines]
    # assert computed_line_depths == expected_line_depths

    assert len(q.tokens) == 20
    assert isinstance(q.tokens[0], Token)

    expected_tokens = [
        Token(type=TokenType.UNTERM_KEYWORD, prefix="", token="select", spos=0, epos=6),
        Token(
            type=TokenType.NAME,
            prefix="\n    ",
            token="a_long_field_name",
            spos=6,
            epos=28,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=28, epos=29),
        Token(
            type=TokenType.NAME,
            prefix="\n    ",
            token="another_long_field_name",
            spos=29,
            epos=57,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=57, epos=58),
        Token(
            type=TokenType.BRACKET_OPEN, prefix="\n    ", token="(", spos=58, epos=64
        ),
        Token(type=TokenType.NAME, prefix="", token="one_field", spos=64, epos=73),
        Token(type=TokenType.OPERATOR, prefix=" ", token="+", spos=73, epos=75),
        Token(type=TokenType.NAME, prefix=" ", token="another_field", spos=75, epos=89),
        Token(type=TokenType.BRACKET_CLOSE, prefix="", token=")", spos=89, epos=90),
        Token(type=TokenType.WORD_OPERATOR, prefix=" ", token="as", spos=90, epos=93),
        Token(type=TokenType.NAME, prefix=" ", token="c", spos=93, epos=95),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="\n", token="from", spos=95, epos=100
        ),
        Token(type=TokenType.NAME, prefix=" ", token="my_schema", spos=100, epos=110),
        Token(type=TokenType.DOT, prefix="", token=".", spos=110, epos=111),
        Token(
            type=TokenType.QUOTED_NAME,
            prefix="",
            token='"my_QUOTED_ table!"',
            spos=111,
            epos=130,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="\n",
            token="where",
            spos=130,
            epos=136,
        ),
        Token(type=TokenType.NAME, prefix=" ", token="one_field", spos=136, epos=146),
        Token(type=TokenType.OPERATOR, prefix=" ", token="<", spos=146, epos=148),
        Token(
            type=TokenType.NAME, prefix=" ", token="another_field", spos=148, epos=162
        ),
    ]

    assert q.tokens == expected_tokens


def test_parsing_error(default_mode: Mode) -> None:
    source_string = "select !"
    with pytest.raises(SqlfmtParsingError):
        _ = Query.from_source(source_string=source_string, mode=default_mode)


def test_whitespace_formatting(default_mode: Mode) -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1 from my_table where true\n"
    q = Query.from_source(source_string=source_string, mode=default_mode)
    assert str(q) == expected_string


def test_case_statement_parsing(default_mode: Mode) -> None:

    source_string, _ = read_test_data(
        "unit_tests/test_parser/test_case_statement_parsing.sql"
    )

    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q
    assert q.source_string == source_string
    assert len([t for t in q.tokens if t.type == TokenType.STATEMENT_START]) == 6
    assert len([t for t in q.tokens if t.type == TokenType.STATEMENT_END]) == 6


def test_cte_parsing(default_mode: Mode) -> None:
    source_string, _ = read_test_data("unit_tests/test_parser/test_cte_parsing.sql")

    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q
    assert q.source_string == source_string

    expected_node_depths = [
        (0, 1),  # with
        (1, 0),  # my_cte
        (1, 0),  # as
        (1, 1),  # (
        (2, 1),  # select
        (3, 0),  # 1
        (3, 0),  # ,
        (3, 0),  # b
        (3, 0),  # ,
        (3, 0),  # another_field
        (2, 1),  # from
        (3, 0),  # my_schema
        (3, 0),  # .
        (3, 0),  # my_table
        (1, 0),  # )
        (0, 1),  # select
        (1, 0),  # *
        (0, 1),  # from
        (1, 0),  # my_cte
    ]

    computed_node_depths = [(node.depth, node.change_in_depth) for node in q.nodes]
    assert computed_node_depths == expected_node_depths


def test_multiline_parsing(default_mode: Mode) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_parser/test_multiline_parsing.sql"
    )

    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q
    assert q.source_string == source_string

    expected = [
        Token(
            type=TokenType.JINJA,
            prefix="",
            token=(
                "{{\n    config(\n        materialized='table',\n        sort='id',\n  "
                "      dist='all',\n        post_hook='grant select on {{ this }} to"
                " role bi_role'\n    )\n}}"
            ),
            spos=0,
            epos=155,
        ),
        Token(
            type=TokenType.COMMENT,
            prefix="\n\n",
            token=(
                "/*\n * This is a typical multiline comment.\n * It contains"
                " newlines.\n * And even /* some {% special characters %}\n * but we're"
                " not going to parse those\n*/"
            ),
            spos=155,
            epos=310,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="\n\n",
            token="with",
            spos=310,
            epos=316,
        ),
        Token(type=TokenType.NAME, prefix="\n    ", token="source", spos=316, epos=327),
        Token(type=TokenType.WORD_OPERATOR, prefix=" ", token="as", spos=327, epos=330),
        Token(type=TokenType.BRACKET_OPEN, prefix=" ", token="(", spos=330, epos=332),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="", token="select", spos=332, epos=338
        ),
        Token(type=TokenType.STAR, prefix=" ", token="*", spos=338, epos=340),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix=" ", token="from", spos=340, epos=345
        ),
        Token(
            type=TokenType.JINJA,
            prefix=" ",
            token="{{ ref('my_model') }}",
            spos=345,
            epos=367,
        ),
        Token(type=TokenType.BRACKET_CLOSE, prefix="", token=")", spos=367, epos=368),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=368, epos=369),
        Token(
            type=TokenType.NAME, prefix="\n    ", token="renamed", spos=369, epos=381
        ),
        Token(type=TokenType.WORD_OPERATOR, prefix=" ", token="as", spos=381, epos=384),
        Token(type=TokenType.BRACKET_OPEN, prefix=" ", token="(", spos=384, epos=386),
        Token(
            type=TokenType.COMMENT,
            prefix=" ",
            token=(
                "/* This is a multiline comment in very bad style,\n    * which starts"
                " and ends on lines with other tokens.\n    */"
            ),
            spos=386,
            epos=499,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="  ",
            token="select",
            spos=499,
            epos=507,
        ),
        Token(
            type=TokenType.NAME, prefix="\n            ", token="id", spos=507, epos=522
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=522, epos=523),
        Token(
            type=TokenType.NAME,
            prefix="\n            ",
            token="another_field",
            spos=523,
            epos=549,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=549, epos=550),
        Token(
            type=TokenType.NAME,
            prefix="\n            ",
            token="and_another",
            spos=550,
            epos=574,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=574, epos=575),
        Token(
            type=TokenType.NAME,
            prefix="\n            ",
            token="and_still_another",
            spos=575,
            epos=605,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="\n        ",
            token="from",
            spos=605,
            epos=618,
        ),
        Token(type=TokenType.NAME, prefix=" ", token="source", spos=618, epos=625),
        Token(
            type=TokenType.BRACKET_CLOSE, prefix="\n    ", token=")", spos=625, epos=631
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=631, epos=632),
        Token(
            type=TokenType.JINJA,
            prefix=" ",
            token=(
                '{% set my_variable_in_bad_style = [\n        "a",\n        "short",\n '
                '       "list",\n        "of",\n        "strings"\n    ] %}'
            ),
            spos=632,
            epos=755,
        ),
        Token(
            type=TokenType.JINJA,
            prefix="\n\n",
            token=(
                "{#\n # And this is a nice multiline jinja comment\n # that we will"
                " also handle.\n#}"
            ),
            spos=755,
            epos=837,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="\n\n",
            token="select",
            spos=837,
            epos=845,
        ),
        Token(type=TokenType.STAR, prefix=" ", token="*", spos=845, epos=847),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix=" ", token="from", spos=847, epos=852
        ),
        Token(type=TokenType.NAME, prefix=" ", token="renamed", spos=852, epos=860),
        Token(
            type=TokenType.COMMENT,
            prefix=" ",
            token="/* what!?! */",
            spos=860,
            epos=874,
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix=" ", token="where", spos=874, epos=880
        ),
        Token(type=TokenType.NAME, prefix=" ", token="true", spos=880, epos=885),
    ]

    assert q.tokens == expected


def test_star_parsing(default_mode: Mode) -> None:
    space_star = "select * from my_table\n"
    space_star_q = Query.from_source(source_string=space_star, mode=default_mode)

    assert space_star_q
    assert len(space_star_q.nodes) == 4
    assert (
        space_star_q.nodes[1].prefix == " "
    ), "There should be a space between select and star in select *"

    dot_star = "select my_table.* from my_table\n"
    dot_star_q = Query.from_source(source_string=dot_star, mode=default_mode)

    assert dot_star_q
    assert len(dot_star_q.nodes) == 6
    assert (
        dot_star_q.nodes[3].prefix == ""
    ), "There should be no space between dot and star in my_table.*"


@pytest.mark.parametrize(
    "source, expected_prefix",
    [
        ("select sum(1)", ""),
        ("over (partition by abc)", " "),
        ("with cte as (select 1)", " "),
        ("select 1 + (1-3)", " "),
        ("where something in (select id from t)", " "),
    ],
)
def test_open_paren_parsing(
    source: str, expected_prefix: str, default_mode: Mode
) -> None:
    q = Query.from_source(source_string=source, mode=default_mode)

    assert q
    for node in q.nodes:
        if node.token.token == "(":
            assert (
                node.prefix == expected_prefix
            ), "Open paren prefixed by wrong number of spaces"


def test_unterminated_multiline_token(default_mode: Mode) -> None:
    source_string = "{% \n config = {}\n"

    with pytest.raises(SqlfmtMultilineError) as excinfo:
        _ = Query.from_source(source_string=source_string, mode=default_mode)

    assert "Unterminated multiline" in str(excinfo.value)
