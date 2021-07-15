from sqlfmt.dialect import Postgres
from sqlfmt.parser import Query
from sqlfmt.token import Token, TokenType


def test_simple_query() -> None:

    with open("tests/data/basic_queries/002_select_from_where.sql") as f:
        source_string = f.read()

    q = Query(source_string=source_string, dialect=Postgres())

    assert q
    assert q.source_string == source_string
    assert len(q.lines) == 6
    assert len(q.tokens) == 25
    assert isinstance(q.tokens[0], Token)

    expected_tokens = [
        Token(
            type=TokenType.TOP_KEYWORD,
            token="select",
            spos=(0, 0),
            epos=(0, 6),
            line="select\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            token="\n",
            spos=(0, 6),
            epos=(0, 7),
            line="select\n",
        ),
        Token(
            type=TokenType.NAME, token="a", spos=(1, 4), epos=(1, 5), line="    a,\n"
        ),
        Token(
            type=TokenType.COMMA, token=",", spos=(1, 5), epos=(1, 6), line="    a,\n"
        ),
        Token(
            type=TokenType.NEWLINE,
            token="\n",
            spos=(1, 6),
            epos=(1, 7),
            line="    a,\n",
        ),
        Token(
            type=TokenType.NAME, token="b", spos=(2, 4), epos=(2, 5), line="    b,\n"
        ),
        Token(
            type=TokenType.COMMA, token=",", spos=(2, 5), epos=(2, 6), line="    b,\n"
        ),
        Token(
            type=TokenType.NEWLINE,
            token="\n",
            spos=(2, 6),
            epos=(2, 7),
            line="    b,\n",
        ),
        Token(
            type=TokenType.BRACKET_OPEN,
            token="(",
            spos=(3, 4),
            epos=(3, 5),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            token="a",
            spos=(3, 5),
            epos=(3, 6),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.OPERATOR,
            token="+",
            spos=(3, 7),
            epos=(3, 8),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            token="b",
            spos=(3, 9),
            epos=(3, 10),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.BRACKET_CLOSE,
            token=")",
            spos=(3, 10),
            epos=(3, 11),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            token="as",
            spos=(3, 12),
            epos=(3, 14),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NAME,
            token="c",
            spos=(3, 15),
            epos=(3, 16),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.NEWLINE,
            token="\n",
            spos=(3, 16),
            epos=(3, 17),
            line="    (a + b) as c\n",
        ),
        Token(
            type=TokenType.TOP_KEYWORD,
            token="from",
            spos=(4, 0),
            epos=(4, 4),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.NAME,
            token="my_schema",
            spos=(4, 5),
            epos=(4, 14),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.DOT,
            token=".",
            spos=(4, 14),
            epos=(4, 15),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.QUOTED_NAME,
            token='"my_QUOTED_ table!"',
            spos=(4, 15),
            epos=(4, 34),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.NEWLINE,
            token="\n",
            spos=(4, 34),
            epos=(4, 35),
            line='from my_schema."my_QUOTED_ table!"\n',
        ),
        Token(
            type=TokenType.TOP_KEYWORD,
            token="where",
            spos=(5, 0),
            epos=(5, 5),
            line="where a < b",
        ),
        Token(
            type=TokenType.NAME, token="a", spos=(5, 6), epos=(5, 7), line="where a < b"
        ),
        Token(
            type=TokenType.OPERATOR,
            token="<",
            spos=(5, 8),
            epos=(5, 9),
            line="where a < b",
        ),
        Token(
            type=TokenType.NAME,
            token="b",
            spos=(5, 10),
            epos=(5, 11),
            line="where a < b",
        ),
    ]

    assert q.tokens == expected_tokens
