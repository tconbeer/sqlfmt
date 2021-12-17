import pytest

from sqlfmt.analyzer import SqlfmtParsingError
from sqlfmt.exception import SqlfmtMultilineError
from sqlfmt.line import Comment, Node, SqlfmtBracketError
from sqlfmt.mode import Mode
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
        "unit_tests/test_query/test_simple_query_parsing.sql"
    )

    q = all_output_modes.dialect.initialize_analyzer(
        all_output_modes.line_length
    ).parse_query(source_string=source_string)

    assert q
    assert q.source_string == source_string
    assert len(q.lines) == 6

    expected_line_depths = [0, 1, 1, 1, 0, 0]
    actual_line_depths = [line.depth for line in q.lines]
    assert actual_line_depths == expected_line_depths

    assert q.nodes

    assert len(q.tokens) == 26
    assert isinstance(q.tokens[0], Token)

    expected_tokens = [
        Token(type=TokenType.UNTERM_KEYWORD, prefix="", token="select", spos=0, epos=6),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=6, epos=7),
        Token(
            type=TokenType.NAME,
            prefix="    ",
            token="a_long_field_name",
            spos=7,
            epos=28,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=28, epos=29),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=29, epos=30),
        Token(
            type=TokenType.NAME,
            prefix="    ",
            token="another_long_field_name",
            spos=30,
            epos=57,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=57, epos=58),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=58, epos=59),
        Token(type=TokenType.BRACKET_OPEN, prefix="    ", token="(", spos=59, epos=64),
        Token(type=TokenType.NAME, prefix="", token="one_field", spos=64, epos=73),
        Token(type=TokenType.OPERATOR, prefix=" ", token="+", spos=73, epos=75),
        Token(type=TokenType.NAME, prefix=" ", token="another_field", spos=75, epos=89),
        Token(type=TokenType.BRACKET_CLOSE, prefix="", token=")", spos=89, epos=90),
        Token(type=TokenType.AS, prefix=" ", token="as", spos=90, epos=93),
        Token(type=TokenType.NAME, prefix=" ", token="c", spos=93, epos=95),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=95, epos=96),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="", token="from", spos=96, epos=100
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
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=130, epos=131),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="", token="where", spos=131, epos=136
        ),
        Token(type=TokenType.NAME, prefix=" ", token="one_field", spos=136, epos=146),
        Token(type=TokenType.OPERATOR, prefix=" ", token="<", spos=146, epos=148),
        Token(
            type=TokenType.NAME, prefix=" ", token="another_field", spos=148, epos=162
        ),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=162, epos=162),
    ]

    assert q.tokens == expected_tokens


def test_parsing_error(default_mode: Mode) -> None:
    source_string = "select !"
    with pytest.raises(SqlfmtParsingError):
        _ = default_mode.dialect.initialize_analyzer(
            default_mode.line_length
        ).parse_query(source_string=source_string)


def test_whitespace_formatting(default_mode: Mode) -> None:
    source_string = "  select 1\n    from my_table\nwhere true"
    expected_string = "select 1\nfrom my_table\nwhere true\n"
    q = default_mode.dialect.initialize_analyzer(default_mode.line_length).parse_query(
        source_string=source_string
    )
    assert str(q) == expected_string


def test_case_statement_parsing(default_mode: Mode) -> None:

    source_string, _ = read_test_data(
        "unit_tests/test_query/test_case_statement_parsing.sql"
    )

    q = default_mode.dialect.initialize_analyzer(default_mode.line_length).parse_query(
        source_string=source_string
    )

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
    source_string, _ = read_test_data("unit_tests/test_query/test_cte_parsing.sql")

    q = default_mode.dialect.initialize_analyzer(default_mode.line_length).parse_query(
        source_string=source_string
    )

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
        "unit_tests/test_query/test_multiline_parsing.sql"
    )

    q = default_mode.dialect.initialize_analyzer(default_mode.line_length).parse_query(
        source_string=source_string
    )

    assert q
    assert q.source_string == source_string
    assert len(q.lines) < len(source_string.split("\n"))

    assert TokenType.COMMENT_START not in [token.type for token in q.tokens]
    assert TokenType.COMMENT_END not in [token.type for token in q.tokens]
    assert TokenType.JINJA_START not in [token.type for token in q.tokens]
    assert TokenType.JINJA_END not in [token.type for token in q.tokens]

    expected_comments = [
        Comment(
            token=Token(
                type=TokenType.COMMENT,
                prefix="",
                token=(
                    "/*\n * This is a typical multiline comment.\n"
                    " * It contains newlines.\n"
                    " * And even /* some {% special characters %}\n"
                    " * but we're not going to parse those\n*/"
                ),
                spos=157,
                epos=310,
            ),
            is_standalone=True,
        ),
        Comment(
            token=Token(
                type=TokenType.COMMENT,
                prefix=" ",
                token=(
                    "/* This is a multiline comment in very bad style,\n"
                    "    * which starts and ends on lines with other tokens.\n    */"
                ),
                spos=386,
                epos=499,
            ),
            is_standalone=True,
        ),
        Comment(
            token=Token(
                type=TokenType.COMMENT,
                prefix="",
                token=(
                    "{#\n # And this is a nice multiline jinja comment\n"
                    " # that we will also handle.\n#}"
                ),
                spos=757,
                epos=837,
            ),
            is_standalone=True,
        ),
        Comment(
            token=Token(
                type=TokenType.COMMENT,
                prefix=" ",
                token="/* what!?! */",
                spos=860,
                epos=874,
            ),
            is_standalone=False,
        ),
    ]

    expected_content = [
        Token(
            type=TokenType.JINJA,
            prefix="",
            token=(
                "{{\n    config(\n        materialized='table',\n        sort='id',\n"
                "        dist='all',\n"
                "        post_hook='grant select on {{ this }} to role bi_role'\n"
                "    )\n}}"
            ),
            spos=0,
            epos=155,
        ),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=155, epos=156),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=156, epos=157),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="", token="with", spos=312, epos=316
        ),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=316, epos=317),
        Token(type=TokenType.NAME, prefix="    ", token="source", spos=317, epos=327),
        Token(type=TokenType.AS, prefix=" ", token="as", spos=327, epos=330),
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
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=369, epos=370),
        Token(type=TokenType.NAME, prefix="    ", token="renamed", spos=370, epos=381),
        Token(type=TokenType.AS, prefix=" ", token="as", spos=381, epos=384),
        Token(type=TokenType.BRACKET_OPEN, prefix=" ", token="(", spos=384, epos=386),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="  ",
            token="select",
            spos=499,
            epos=507,
        ),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=507, epos=508),
        Token(
            type=TokenType.NAME, prefix="            ", token="id", spos=508, epos=522
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=522, epos=523),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=523, epos=524),
        Token(
            type=TokenType.NAME,
            prefix="            ",
            token="another_field",
            spos=524,
            epos=549,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=549, epos=550),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=550, epos=551),
        Token(
            type=TokenType.NAME,
            prefix="            ",
            token="and_another",
            spos=551,
            epos=574,
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=574, epos=575),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=575, epos=576),
        Token(
            type=TokenType.NAME,
            prefix="            ",
            token="and_still_another",
            spos=576,
            epos=605,
        ),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=605, epos=606),
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="        ",
            token="from",
            spos=606,
            epos=618,
        ),
        Token(type=TokenType.NAME, prefix=" ", token="source", spos=618, epos=625),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=625, epos=626),
        Token(
            type=TokenType.BRACKET_CLOSE, prefix="    ", token=")", spos=626, epos=631
        ),
        Token(type=TokenType.COMMA, prefix="", token=",", spos=631, epos=632),
        Token(
            type=TokenType.JINJA,
            prefix=" ",
            token=(
                '{% set my_variable_in_bad_style = [\n        "a",\n'
                '        "short",\n        "list",\n        "of",\n'
                '        "strings"\n    ] %}'
            ),
            spos=632,
            epos=755,
        ),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=755, epos=756),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=756, epos=757),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix="", token="select", spos=839, epos=845
        ),
        Token(type=TokenType.STAR, prefix=" ", token="*", spos=845, epos=847),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix=" ", token="from", spos=847, epos=852
        ),
        Token(type=TokenType.NAME, prefix=" ", token="renamed", spos=852, epos=860),
        Token(
            type=TokenType.UNTERM_KEYWORD, prefix=" ", token="where", spos=874, epos=880
        ),
        Token(type=TokenType.NAME, prefix=" ", token="true", spos=880, epos=885),
        Token(type=TokenType.NEWLINE, prefix="", token="\n", spos=885, epos=885),
    ]

    actual_comments = []
    for line in q.lines:
        actual_comments.extend(line.comments)
    assert actual_comments == expected_comments
    assert q.tokens == expected_content


def test_star_parsing(default_mode: Mode) -> None:
    space_star = "select * from my_table\n"
    space_star_q = default_mode.dialect.initialize_analyzer(
        default_mode.line_length
    ).parse_query(source_string=space_star)

    assert space_star_q
    assert len(space_star_q.nodes) == 5
    assert (
        space_star_q.nodes[1].prefix == " "
    ), "There should be a space between select and star in select *"

    dot_star = "select my_table.* from my_table\n"
    dot_star_q = default_mode.dialect.initialize_analyzer(
        default_mode.line_length
    ).parse_query(source_string=dot_star)

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
    q = default_mode.dialect.initialize_analyzer(default_mode.line_length).parse_query(
        source_string=source
    )

    assert q
    for node in q.nodes:
        if node.token.token == "(":
            assert (
                node.prefix == expected_prefix
            ), "Open paren prefixed by wrong number of spaces"


def test_unterminated_multiline_token(default_mode: Mode) -> None:
    source_string = "{% \n config = {}\n"

    with pytest.raises(SqlfmtMultilineError) as excinfo:
        _ = default_mode.dialect.initialize_analyzer(
            default_mode.line_length
        ).parse_query(source_string=source_string)

    assert "Unterminated multiline" in str(excinfo.value)


def test_unmatched_bracket_error(default_mode: Mode) -> None:
    source_string = "select ( end\n"
    with pytest.raises(SqlfmtBracketError) as excinfo:
        _ = default_mode.dialect.initialize_analyzer(
            default_mode.line_length
        ).parse_query(source_string=source_string)

    assert "Closing bracket 'end'" in str(excinfo.value)
