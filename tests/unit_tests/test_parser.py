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

    assert len(q.tokens) == 25
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
            token="a",
            spos=(1, 4),
            epos=(1, 5),
            line="    a,\n",
        ),
        Token(
            type=TokenType.COMMA,
            prefix="",
            token=",",
            spos=(1, 5),
            epos=(1, 6),
            line="    a,\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(1, 6),
            epos=(1, 7),
            line="    a,\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix="    ",
            token="b",
            spos=(2, 4),
            epos=(2, 5),
            line="    b,\n",
        ),
        Token(
            type=TokenType.COMMA,
            prefix="",
            token=",",
            spos=(2, 5),
            epos=(2, 6),
            line="    b,\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(2, 6),
            epos=(2, 7),
            line="    b,\n",
        ),
        Token(
            type=TokenType.BRACKET_OPEN,
            prefix="    ",
            token="(",
            spos=(3, 4),
            epos=(3, 5),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix="",
            token="a",
            spos=(3, 5),
            epos=(3, 6),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="+",
            spos=(3, 7),
            epos=(3, 8),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="b",
            spos=(3, 9),
            epos=(3, 10),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.BRACKET_CLOSE,
            prefix="",
            token=")",
            spos=(3, 10),
            epos=(3, 11),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="as",
            spos=(3, 12),
            epos=(3, 14),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="c",
            spos=(3, 15),
            epos=(3, 16),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=(3, 16),
            epos=(3, 17),
            line="    (a + b) as c\n",
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
            line="where a < b",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="a",
            spos=(5, 6),
            epos=(5, 7),
            line="where a < b",
        ),
        Token(
            type=TokenType.OPERATOR,
            prefix=" ",
            token="<",
            spos=(5, 8),
            epos=(5, 9),
            line="where a < b",
        ),
        Token(
            type=TokenType.NAME,
            prefix=" ",
            token="b",
            spos=(5, 10),
            epos=(5, 11),
            line="where a < b",
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
    ]

    assert q.tokens == expected_tokens


def test_whitespace_formatting() -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1\nfrom my_table\nwhere true"
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
    ]

    computed_node_depths = [(node.depth, node.change_in_depth) for node in q.nodes]
    assert computed_node_depths == expected_node_depths
