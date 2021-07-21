import pytest

from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.splitter import LineSplitter


class TestSplitter:
    @pytest.fixture(scope="class")
    def depth_split_line(self) -> Line:
        source_string = "with my_cte as (select 1, b from my_schema.my_table),\n"
        mode = Mode()
        raw_query = Query.from_source(source_string, mode)
        return raw_query.lines[0]

    @pytest.fixture(scope="class")
    def splitter(self) -> LineSplitter:
        mode = Mode()
        return LineSplitter(mode)

    def test_maybe_split(self, splitter: LineSplitter, depth_split_line: Line) -> None:
        assert depth_split_line.change_in_depth == 1

        line_gen = splitter.maybe_split(depth_split_line)

        first_line = next(line_gen)
        assert str(first_line) == "with\n"

        second_line = next(line_gen)
        assert (
            str(second_line)
            == " " * 4 + "my_cte as (select 1, b from my_schema.my_table),\n"
        )

        with pytest.raises(StopIteration):
            next(line_gen)
