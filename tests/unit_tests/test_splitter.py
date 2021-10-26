import pytest

from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.splitter import LineSplitter


@pytest.fixture
def mode() -> Mode:
    return Mode()


@pytest.fixture
def splitter(mode: Mode) -> LineSplitter:
    return LineSplitter(mode)


@pytest.fixture
def depth_split_line(mode: Mode) -> Line:
    source_string = "with my_cte as (select 1, b from my_schema.my_table),\n"
    raw_query = Query.from_source(source_string, mode)
    return raw_query.lines[0]


def test_maybe_split(splitter: LineSplitter, depth_split_line: Line) -> None:
    assert depth_split_line.change_in_depth == 1

    line_gen = splitter.maybe_split(depth_split_line)
    result = list(map(str, line_gen))

    expected = [
        "with\n",
        " " * 4 + "my_cte as (\n",
        " " * 8 + "select\n",
        " " * 12 + "1,\n",
        " " * 12 + "b\n",
        " " * 8 + "from\n",
        " " * 12 + "my_schema.my_table\n",
        " " * 4 + "),\n",
    ]

    assert result == expected


def test_split_one_liner(splitter: LineSplitter) -> None:
    source_string = "select * from my_table\n"
    raw_query = Query.from_source(source_string, splitter.mode)

    for raw_line in raw_query.lines:
        splits = splitter.maybe_split(raw_line)
        result = list(splits)
        assert len(result) == 4


def test_cannot_depth_split(splitter: LineSplitter) -> None:
    source_string = (
        "one_field + another_field, another_field + one_more_field "
        " + one_more_field + another_really_really_long_field_name\n"
    )
    raw_query = Query.from_source(source_string, splitter.mode)
    line = raw_query.lines[0]

    gen = splitter.split(line, kind="depth")
    split_line = next(gen)

    assert split_line == line

    with pytest.raises(StopIteration):
        next(gen)


def test_cannot_comma_split(splitter: LineSplitter) -> None:
    source_string = (
        "select another_field + (another_field + one_more_field "
        " + one_more_field) + another_really_really_long_field_name\n"
    )
    raw_query = Query.from_source(source_string, splitter.mode)
    line = raw_query.lines[0]

    gen = splitter.split(line, kind="comma")
    split_line = next(gen)

    assert split_line == line

    with pytest.raises(StopIteration):
        next(gen)
