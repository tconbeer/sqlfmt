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
        spos=(0, 0),
        epos=(0, 6),
        line="select\n",
    )
    res = Node.calculate_depth(t, inherited_depth=0, open_brackets=[])

    assert res == (0, 1, [t])

    t = Token(
        type=TokenType.BRACKET_CLOSE,
        prefix="",
        token=")",
        spos=(3, 10),
        epos=(3, 11),
        line="    (a + b) as c\n",
    )

    b = Token(
        type=TokenType.BRACKET_OPEN,
        prefix="    ",
        token="(",
        spos=(3, 4),
        epos=(3, 5),
        line="    (a + b) as c\n",
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
    assert len(q.lines) == 6

    expected_line_depths = [0, 1, 1, 1, 0, 0]

    computed_line_depths = [line.depth for line in q.lines]
    assert computed_line_depths == expected_line_depths

    assert len(q.tokens) == 26
    assert isinstance(q.tokens[0], Token)

    expected_tokens = [
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="",
            token="select",
            spos=(0, 0),
            epos=(0, 6),
            line="select\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(0, 6),
            epos=(0, 7),
            line="select\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix="    ",
            token="a_long_field_name",
            spos=(1, 4),
            epos=(1, 21),
            line="    a_long_field_name,\n",
        ),
        Token(
            type=TokenType.COMMA,
            prefix="",
            token=",",
            spos=(1, 21),
            epos=(1, 22),
            line="    a_long_field_name,\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(1, 22),
            epos=(1, 23),
            line="    a_long_field_name,\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix="    ",
            token="another_long_field_name",
            spos=(2, 4),
            epos=(2, 27),
            line="    another_long_field_name,\n",
        ),
        Token(
            type=TokenType.COMMA,
            prefix="",
            token=",",
            spos=(2, 27),
            epos=(2, 28),
            line="    another_long_field_name,\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(2, 28),
            epos=(2, 29),
            line="    another_long_field_name,\n",
        ),
        Token(
            type=TokenType.BRACKET_OPEN,
            prefix="    ",
            token="(",
            spos=(3, 4),
            epos=(3, 5),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix="",
            token="one_field",
            spos=(3, 5),
            epos=(3, 14),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="+",
            spos=(3, 15),
            epos=(3, 16),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="another_field",
            spos=(3, 17),
            epos=(3, 30),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.BRACKET_CLOSE,
            prefix="",
            token=")",
            spos=(3, 30),
            epos=(3, 31),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="as",
            spos=(3, 32),
            epos=(3, 34),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="c",
            spos=(3, 35),
            epos=(3, 36),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(3, 36),
            epos=(3, 37),
            line="    (one_field + another_field) as c\n",
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="",
            token="from",
            spos=(4, 0),
            epos=(4, 4),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="my_schema",
            spos=(4, 5),
            epos=(4, 14),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.DOT,
            prefix="",
            token=".",
            spos=(4, 14),
            epos=(4, 15),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.QUOTED_NAME,
            prefix="",
            token='"my_QUOTED_ table!"',
            spos=(4, 15),
            epos=(4, 34),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(4, 34),
            epos=(4, 35),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="",
            token="where",
            spos=(5, 0),
            epos=(5, 5),
            line="where one_field < another_field\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="one_field",
            spos=(5, 6),
            epos=(5, 15),
            line="where one_field < another_field\n",
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="<",
            spos=(5, 16),
            epos=(5, 17),
            line="where one_field < another_field\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="another_field",
            spos=(5, 18),
            epos=(5, 31),
            line="where one_field < another_field\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(5, 31),
            epos=(5, 32),
            line="where one_field < another_field\n",
        ),
    ]

    assert q.tokens == expected_tokens


def test_parsing_error(default_mode: Mode) -> None:
    source_string = "select !"
    with pytest.raises(SqlfmtParsingError):
        _ = Query.from_source(source_string=source_string, mode=default_mode)


def test_whitespace_formatting(default_mode: Mode) -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1\nfrom my_table\nwhere true\n"
    q = Query.from_source(source_string=source_string, mode=default_mode)
    assert str(q) == expected_string


def test_case_statement_parsing(default_mode: Mode) -> None:

    source_string, _ = read_test_data(
        "unit_tests/test_parser/test_case_statement_parsing.sql"
    )

    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q
    assert q.source_string == source_string
    assert len(q.lines) == 20

    expected_line_depths = [0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 2, 3, 1, 1, 2, 1, 1, 1, 1, 0]

    computed_line_depths = [line.depth for line in q.lines]
    assert computed_line_depths == expected_line_depths

    # there are 6 case statements in the test data
    assert len([t for t in q.tokens if t.type == TokenType.STATEMENT_START]) == 6
    assert len([t for t in q.tokens if t.type == TokenType.STATEMENT_END]) == 6


def test_cte_parsing(default_mode: Mode) -> None:
    source_string, _ = read_test_data("unit_tests/test_parser/test_cte_parsing.sql")

    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q
    assert q.source_string == source_string
    assert len(q.lines) == 3

    expected_line_depths = [0, 1, 0]

    computed_line_depths = [line.depth for line in q.lines]
    assert computed_line_depths == expected_line_depths

    expected_node_depths = [
        (0, 1),  # with
        (1, 0),  # \n
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
        (1, 0),  # \n
        (0, 1),  # select
        (1, 0),  # *
        (0, 1),  # from
        (1, 0),  # my_cte
        (1, 0),  # \n
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
    assert len(q.lines) < len(source_string.split("\n"))
    assert len(q.tokens) == 56

    assert TokenType.COMMENT_START not in [token.type for token in q.tokens]
    assert TokenType.COMMENT_END not in [token.type for token in q.tokens]
    assert TokenType.JINJA_START not in [token.type for token in q.tokens]
    assert TokenType.JINJA_END not in [token.type for token in q.tokens]

    expected = [
        (
            "{{\n"
            "    config(\n"
            "        materialized='table',\n"
            "        sort='id',\n"
            "        dist='all',\n"
            "        post_hook='grant select on {{ this }} to role bi_role'\n"
            "    )\n"
            "}}"
        ),
        (
            "/*\n"
            " * This is a typical multiline comment.\n"
            " * It contains newlines.\n"
            " * And even /* some {% special characters %} */\n"
            " * but we're not going to parse those\n"
            "*/"
        ),
        (
            "/* This is a multiline comment in very bad style,\n"
            "    * which starts and ends on lines with other tokens.\n"
            "    */"
        ),
        (
            "{% set my_variable_in_bad_style = [\n"
            '        "a",\n'
            '        "short",\n'
            '        "list",\n'
            '        "of",\n'
            '        "strings"\n'
            "    ] %}"
        ),
        (
            "{#\n"
            " # And this is a nice multiline jinja comment\n"
            " # that we will also handle.\n"
            "#}"
        ),
    ]

    assert q.tokens[0].token == expected[0]
    assert q.tokens[3].token == expected[1]

    source = (
        "    renamed as ( /* This is a multiline comment in very bad style,\n"
        "    * which starts and ends on lines with other tokens.\n"
        "    */  select\n"
    )
    assert q.tokens[21].token == expected[2]
    assert q.tokens[21].line == source

    assert q.tokens[41].token == expected[3]
    assert q.tokens[44].token == expected[4]

    assert [node.token.type for node in q.lines[0].nodes] == [
        TokenType.JINJA,
        TokenType.NEWLINE,
    ]
    assert [node.token.type for node in q.lines[2].nodes] == [
        TokenType.COMMENT,
        TokenType.NEWLINE,
    ]
    assert [node.token.type for node in q.lines[6].nodes] == [
        TokenType.NAME,
        TokenType.NAME,
        TokenType.BRACKET_OPEN,
        TokenType.COMMENT,
        TokenType.NEWLINE,
    ]
    assert [node.token.type for node in q.lines[7].nodes] == [
        TokenType.UNTERM_KEYWORD,
        TokenType.NEWLINE,
    ]
    assert (q.lines[7].depth, q.lines[7].change_in_depth) == (2, 1)
    assert [node.token.type for node in q.lines[13].nodes] == [
        TokenType.BRACKET_CLOSE,
        TokenType.COMMA,
        TokenType.JINJA,
        TokenType.NEWLINE,
    ]
    assert [node.token.type for node in q.lines[14].nodes] == [TokenType.NEWLINE]
    assert [node.token.type for node in q.lines[15].nodes] == [
        TokenType.JINJA,
        TokenType.NEWLINE,
    ]
    assert [node.token.type for node in q.lines[17].nodes] == [
        TokenType.UNTERM_KEYWORD,
        TokenType.STAR,
        TokenType.UNTERM_KEYWORD,
        TokenType.NAME,
        TokenType.COMMENT,
        TokenType.NEWLINE,
    ]
    assert [node.token.type for node in q.lines[18].nodes] == [
        TokenType.UNTERM_KEYWORD,
        TokenType.NAME,
        TokenType.NEWLINE,
    ]


def test_multiline_wrapping(default_mode: Mode) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_parser/test_multiline_wrapping.sql"
    )

    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q
    assert q.source_string == source_string

    lines_after_parsing = [str(line).strip() for line in q.lines]

    assert "a," in lines_after_parsing, "Should split line after multiline comment"
    assert "as b," not in lines_after_parsing, "Should not split after multiline jinja"
    assert "," not in lines_after_parsing, "Should not split line after multiline jinja"
    assert "c" in lines_after_parsing, "shouldn't impact subsequent lines"


def test_star_parsing(default_mode: Mode) -> None:
    space_star = "select * from my_table\n"
    space_star_q = Query.from_source(source_string=space_star, mode=default_mode)

    assert space_star_q
    assert len(space_star_q.nodes) == 5
    assert (
        space_star_q.nodes[1].prefix == " "
    ), "There should be a space between select and star in select *"

    dot_star = "select my_table.* from my_table\n"
    dot_star_q = Query.from_source(source_string=dot_star, mode=default_mode)

    assert dot_star_q
    assert len(dot_star_q.nodes) == 7
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


def test_dont_parse_twice(default_mode: Mode, monkeypatch: pytest.MonkeyPatch) -> None:
    source_string = "select 1, 2, 3 from my_table where a = b"
    q = Query.from_source(source_string=source_string, mode=default_mode)

    assert q.lines and q.tokens

    # should raise a name error if we parse source again
    monkeypatch.delattr("sqlfmt.dialect.Polyglot.tokenize_line")
    q.tokenize_from_source()
    assert q.lines and q.tokens


def test_unterminated_multiline_token(default_mode: Mode) -> None:
    source_string = "{% \n config = {}\n"

    with pytest.raises(SqlfmtMultilineError) as excinfo:
        _ = Query.from_source(source_string=source_string, mode=default_mode)

    assert "Unterminated multiline" in str(excinfo.value)
