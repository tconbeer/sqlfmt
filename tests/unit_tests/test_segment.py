from typing import List

import pytest
from sqlfmt.analyzer import Analyzer
from sqlfmt.exception import SqlfmtSegmentError
from sqlfmt.line import Line
from sqlfmt.segment import Segment, create_segments_from_lines

from tests.util import read_test_data


@pytest.mark.parametrize(
    "source_string,expected_result",
    [
        ("case\nfoo\nend\n", True),
        ("count(\n*\n)\n", True),
        ("count(\n*\n)\n\n\n", True),
        ("\n\n\ncount(\n*\n)", True),
        ("as (\nselect\n1\n)\n", True),
        ("as foo\n", False),
        ("from\nfoo\nwhere\n", False),
    ],
)
def test_tail_closes_head(
    default_analyzer: Analyzer, source_string: str, expected_result: bool
) -> None:
    q = default_analyzer.parse_query(source_string)
    segment = Segment(q.lines)
    assert segment.tail_closes_head == expected_result


def test_tail_closes_head_empty(default_analyzer: Analyzer) -> None:
    q = default_analyzer.parse_query("a\n\n\n\n\n\n\n\nb\n")
    blank_lines = q.lines[1:-1]
    assert all(line.is_blank_line for line in blank_lines)
    segment = Segment(blank_lines)
    assert segment.tail_closes_head is False


@pytest.mark.parametrize(
    "source_string,expected_idx",
    [
        ("case\nfoo\nend\n", 0),
        ("\n\n\ncount(\n*\n)", 3),
        ("\n\n\n    count(\n*\n)", 3),
        ("\n     \n\n    count(\n*\n)", 3),
    ],
)
def test_segment_head(
    default_analyzer: Analyzer, source_string: str, expected_idx: int
) -> None:
    q = default_analyzer.parse_query(source_string)
    segment = Segment(q.lines)
    line, i = segment.head
    assert i == expected_idx
    assert line == q.lines[i]


@pytest.mark.parametrize(
    "source_string",
    [
        "",
        "\n",
        "\n\n\n    \n\n",
    ],
)
def test_segment_head_raises(default_analyzer: Analyzer, source_string: str) -> None:
    q = default_analyzer.parse_query(source_string)
    segment = Segment(q.lines)
    with pytest.raises(SqlfmtSegmentError):
        _, _ = segment.head


@pytest.mark.parametrize(
    "source_string,expected_idx",
    [
        ("case\nfoo\nend,\na\n", 0),
        ("count(\n*\n),\n\n\na\n", 2),
    ],
)
def test_segment_tail(
    default_analyzer: Analyzer, source_string: str, expected_idx: int
) -> None:
    q = default_analyzer.parse_query(source_string)
    # the parser eliminates trailing empty lines, so
    # we need to add a nonblank line to our test cases
    # and then strip that away
    segment = Segment(q.lines[:-1])
    line, i = segment.tail
    assert i == expected_idx
    assert line == segment[-(i + 1)]


@pytest.mark.parametrize(
    "source_string",
    [
        "",
        "\n",
        "\n\n\n    \n\n",
    ],
)
def test_segment_tail_raises(default_analyzer: Analyzer, source_string: str) -> None:
    q = default_analyzer.parse_query(source_string)
    segment = Segment(q.lines)
    with pytest.raises(SqlfmtSegmentError):
        _, _ = segment.tail


def test_split_into_segments(default_analyzer: Analyzer) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_merger/test_split_into_segments.sql"
    )
    q = default_analyzer.parse_query(source_string)

    top_level_segments = create_segments_from_lines(q.lines)

    assert len(top_level_segments) == 2
    assert str(top_level_segments[0][0]).startswith("select")
    assert str(top_level_segments[1][0]).startswith("from")

    select_segment = [top_level_segments[0]]

    assert select_segment == create_segments_from_lines(select_segment[0])

    select_lines = select_segment[0]
    assert not (
        select_lines[-1].closes_bracket_from_previous_line
        and select_lines[-1].depth == select_lines[0].depth
    )

    indented_segments = create_segments_from_lines(select_lines[1:])
    expected_segments = [
        "    my_first_field,\n",
        "    my_second_field\n",
        "    as an_alias,\n",
        "    case\n",
        "    as my_case_statement,\n",
        "    case\n",
        "    case\n",
        "    ::numeric(\n",
        "    as casted_case\n",
        "    ,\n",
        "    (\n",
        "    +\n",
        "    ::varchar(\n",
        "    another_field,\n",
        "    case\n",
        "    + 4\n",
    ]
    assert [str(segment[0]) for segment in indented_segments] == expected_segments


def test_split_into_segments_empty() -> None:
    no_lines: List[Line] = []
    result = create_segments_from_lines(no_lines)
    assert result == []


@pytest.mark.parametrize(
    "source_string,idx,expected_len",
    [
        ("count(\nfoo\n)\n", 0, 2),
        ("\n\n\n\ncount(\nfoo\n)\n", 4, 2),
        ("foo,\nbar,\nbaz\n", 0, 1),
    ],
)
def test_split_after(
    default_analyzer: Analyzer, source_string: str, idx: int, expected_len: int
) -> None:
    q = default_analyzer.parse_query(source_string)
    segment = Segment(q.lines)
    remainder = segment.split_after(idx)
    first_word = source_string.lstrip().splitlines(keepends=True)[0]
    assert first_word not in [str(line) for s in remainder for line in s]
    assert len(remainder) == expected_len
