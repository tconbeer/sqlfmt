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

    def test_split_one_liner(self, splitter: LineSplitter) -> None:
        source_string = "select * from my_table\n"

        mode = Mode()
        raw_query = Query.from_source(source_string, mode)

        for raw_line in raw_query.lines:
            splits = splitter.maybe_split(raw_line)
            result = list(splits)
            assert len(result) == 4
