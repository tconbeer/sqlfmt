from typing import List

import pytest

from sqlfmt.analyzer import Analyzer
from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.node_manager import NodeManager
from sqlfmt.splitter import LineSplitter
from tests.util import read_test_data


@pytest.fixture
def splitter(default_mode: Mode) -> LineSplitter:
    node_manager = NodeManager(default_mode.dialect.case_sensitive_names)
    return LineSplitter(node_manager)


@pytest.fixture
def default_analyzer(default_mode: Mode) -> Analyzer:
    return default_mode.dialect.initialize_analyzer(default_mode.line_length)


@pytest.fixture
def depth_split_line(default_analyzer: Analyzer) -> Line:
    source_string = "with my_cte as (select 1, b from my_schema.my_table),\n"
    raw_query = default_analyzer.parse_query(source_string)
    return raw_query.lines[0]


def test_maybe_split(splitter: LineSplitter, depth_split_line: Line) -> None:
    line_gen = splitter.maybe_split(depth_split_line)
    result = list(map(str, line_gen))

    expected = [
        "with\n",
        " " * 4 + "my_cte\n",
        " " * 4 + "as (\n",
        " " * 8 + "select\n",
        " " * 12 + "1,\n",
        " " * 12 + "b\n",
        " " * 8 + "from\n",
        " " * 12 + "my_schema.my_table\n",
        " " * 4 + "),\n",
    ]

    assert result == expected


def test_split_one_liner(splitter: LineSplitter, default_analyzer: Analyzer) -> None:
    source_string = "select * from my_table\n"
    raw_query = default_analyzer.parse_query(source_string)

    for raw_line in raw_query.lines:
        splits = splitter.maybe_split(raw_line)
        result = list(splits)
        assert len(result) == 4


def test_simple_comment_split(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string, expected_result = read_test_data(
        "unit_tests/test_splitter/test_simple_comment_split.sql"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = "".join([str(line) for line in split_lines])

    assert actual_result == expected_result

    expected_comments = [
        (
            "-- not distinct, just an ordinary select here,"
            " no big deal at all, it's okay really\n"
        ),
        "-- here is a long comment to be wrapped above this line\n",
        "",
        "-- a short comment\n",
        "-- here is another long comment to be wrapped but not indented\n",
        "",
        "-- another comment that is a little bit too long to stay here\n",
        "",
        "-- this should stay\n",
        "",
        "-- one last comment\n",
    ]

    for i, line in enumerate(split_lines):
        if line.comments:
            assert str(line.comments[0]) == expected_comments[i]


def test_split_count_window_function(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string = (
        "count(case when a is null then 1 end) over "
        "(partition by user_id, date_trunc('year', performed_at)) as d,\n"
    )
    expected_result = (
        "count(\n"
        "    case\n"
        "        when\n"
        "            a\n"
        "            is null\n"
        "        then\n"
        "            1\n"
        "    end\n"
        ")\n"
        "over (\n"
        "    partition by\n"
        "        user_id,\n"
        "        date_trunc(\n"
        "            'year',\n"
        "            performed_at\n"
        "        )\n"
        ")\n"
        "as d,\n"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = "".join([str(line) for line in split_lines])

    assert actual_result == expected_result


def test_split_function_no_args(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string = "sum(a) over () as a,\nrow_number() over () as b,\n"
    expected_result = [
        "sum(\n",
        "    a\n",
        ")\n",
        "over (\n",
        ")\n",
        "as a,\n",
        "row_number(\n",
        ")\n",
        "over (\n",
        ")\n",
        "as b,\n",
    ]
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]

    assert actual_result == expected_result


def test_comment_split_impact_on_open_brackets(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string, expected_result = read_test_data(
        "unit_tests/test_splitter/test_comment_split_impact_on_open_brackets.sql"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = "".join([str(line) for line in split_lines])
    assert actual_result == expected_result


def test_split_long_line_on_operator(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string = (
        "a_really_long_field + a_really_really_really_long_field "
        "+ a_really_really_really_really_long_field as another_field\n"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    expected_result = [
        "a_really_long_field\n",
        "+ a_really_really_really_long_field\n",
        "+ a_really_really_really_really_long_field\n",
        "as another_field\n",
    ]
    assert actual_result == expected_result


def test_split_at_star(splitter: LineSplitter, default_analyzer: Analyzer) -> None:
    source_string = "select *, my_table.*, 1 * 1, a_field * b_field from my_table\n"
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    expected_result = [
        "select\n",
        "    *,\n",
        "    my_table.*,\n",
        "    1\n",
        "    * 1,\n",
        "    a_field\n",
        "    * b_field\n",
        "from\n",
        "    my_table\n",
    ]
    assert actual_result == expected_result


def test_jinja_block_split(splitter: LineSplitter, default_analyzer: Analyzer) -> None:
    source_string, expected_result = read_test_data(
        "unit_tests/test_splitter/test_jinja_block_split.sql"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = "".join([str(line).lstrip() for line in split_lines])

    assert actual_result == expected_result


def test_split_at_and(splitter: LineSplitter, default_analyzer: Analyzer) -> None:
    source_string = "select 1 where a between b and c and d between e and f and a < b\n"
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    expected_result = [
        "select\n",
        "    1\n",
        "where\n",
        "    a\n",
        "    between b\n",
        "    and c\n",
        "    and d\n",
        "    between e\n",
        "    and f\n",
        "    and a\n",
        "    < b\n",
    ]
    assert actual_result == expected_result


def test_split_before_semicolon(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string = "select 1; select 2; select 3; select 4;\n"
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    expected_result = [
        "select\n",
        "    1\n",
        ";\n",
        "select\n",
        "    2\n",
        ";\n",
        "select\n",
        "    3\n",
        ";\n",
        "select\n",
        "    4\n",
        ";\n",
    ]
    assert actual_result == expected_result


def test_split_around_set_operator(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string = (
        "select 1 union all select 2 union all (select 3) union all select 4\n"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    expected_result = [
        "select\n",
        "    1\n",
        "union all\n",
        "select\n",
        "    2\n",
        "union all\n",
        "(\n",
        "    select\n",
        "        3\n",
        ")\n",
        "union all\n",
        "select\n",
        "    4\n",
    ]
    assert actual_result == expected_result


def test_split_between_brackets(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string = "select split(my_string, ',')[offset(0)], my_dict['tlk']('arg')\n"
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    expected_result = [
        "select\n",
        "    split(\n",
        "        my_string,\n",
        "        ','\n",
        "    )\n",
        "    [\n",
        "        offset(\n",
        "            0\n",
        "        )\n",
        "    ],\n",
        "    my_dict\n",
        "    [\n",
        "        'tlk'\n",
        "    ]\n",
        "    (\n",
        "        'arg'\n",
        "    )\n",
    ]
    assert actual_result == expected_result


def test_split_around_data(splitter: LineSplitter, default_analyzer: Analyzer) -> None:
    source_string = "{% set foo %}//my one-line //data{% endset %}\n"
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))

    actual_result = [str(line) for line in split_lines]
    assert actual_result == [source_string]


def test_can_split_very_long_lines(
    splitter: LineSplitter, default_analyzer: Analyzer
) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_splitter/test_very_long_single_line.sql"
    )
    raw_query = default_analyzer.parse_query(source_string)

    split_lines: List[Line] = []

    # just make sure this doesn't raise a maximum recursion depth error
    for raw_line in raw_query.lines:
        split_lines.extend(splitter.maybe_split(raw_line))
