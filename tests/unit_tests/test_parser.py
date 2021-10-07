from sqlfmt.mode import Mode
from sqlfmt.parser import Node, Query
from sqlfmt.token import Token, TokenType


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


def test_simple_query_parsing() -> None:

    with open("tests/data/basic_queries/002_select_from_where.sql") as f:
        source_string = f.read()

    q = Query.from_source(source_string=source_string, mode=Mode())

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
            line="where one_field < another_field",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="one_field",
            spos=(5, 6),
            epos=(5, 15),
            line="where one_field < another_field",
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="<",
            spos=(5, 16),
            epos=(5, 17),
            line="where one_field < another_field",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="another_field",
            spos=(5, 18),
            epos=(5, 31),
            line="where one_field < another_field",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(5, 31),
            epos=(5, 32),
            line="where one_field < another_field",
        ),
    ]

    assert q.tokens == expected_tokens


def test_error_token() -> None:
    source_string = "select `no backticks in postgres`"
    q = Query.from_source(source_string=source_string, mode=Mode())

    expected_tokens = [
        Token(
            TokenType.UNTERM_KEYWORD,
            "",
            "select",
            (0, 0),
            (0, 6),
            source_string,
        ),
        Token(
            TokenType.ERROR_TOKEN,
            " ",
            "`no backticks in postgres`",
            (0, 6),
            (0, len(source_string)),
            source_string,
        ),
        Token(
            TokenType.NEWLINE,
            "",
            "\n",
            (0, len(source_string)),
            (0, len(source_string) + 1),
            source_string,
        ),
    ]

    assert q.tokens == expected_tokens


def test_whitespace_formatting() -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1\nfrom my_table\nwhere true\n"
    q = Query.from_source(source_string=source_string, mode=Mode())
    assert str(q) == expected_string


def test_case_statement_parsing() -> None:

    with open("tests/data/basic_queries/003_select_case.sql") as f:
        source_string = f.read()

    q = Query.from_source(source_string=source_string, mode=Mode())

    assert q
    assert q.source_string == source_string
    assert len(q.lines) == 18

    expected_line_depths = [0, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2, 1, 1, 1, 1, 0]

    computed_line_depths = [line.depth for line in q.lines]
    assert computed_line_depths == expected_line_depths

    # there are 6 case statements in the test data
    assert len([t for t in q.tokens if t.type == TokenType.STATEMENT_START]) == 6
    assert len([t for t in q.tokens if t.type == TokenType.STATEMENT_END]) == 6


def test_cte_parsing() -> None:
    with open("tests/data/basic_queries/004_with_select.sql") as f:
        source_string = f.read()

    q = Query.from_source(source_string=source_string, mode=Mode())

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


def test_multiline_parsing() -> None:
    with open("tests/data/basic_queries/005_multiline.sql") as f:
        source_string = f.read()

    q = Query.from_source(source_string=source_string, mode=Mode())

    assert q
    assert q.source_string == source_string
    assert len(q.lines) < len(source_string.split("\n"))
    assert len(q.tokens) == 56

    assert TokenType.ERROR_TOKEN not in [token.type for token in q.tokens]
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
        TokenType.OPERATOR,
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
