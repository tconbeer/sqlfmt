import itertools
from typing import List

import pytest

from sqlfmt.exception import SqlfmtSegmentError
from sqlfmt.line import Line
from sqlfmt.merger import CannotMergeException, LineMerger
from sqlfmt.mode import Mode
from tests.util import read_test_data


@pytest.fixture
def merger(default_mode: Mode) -> LineMerger:
    return LineMerger(default_mode)


def test_create_merged_line(merger: LineMerger) -> None:

    source_string = """
    select
        able,
        baker,
        /*  a
            multiline
            comment
        */




        charlie,





        delta,
    """
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)

    expected = "\nselect able, baker,\n"
    merged = merger.create_merged_line(raw_query.lines[0:4])
    actual = "".join([str(line) for line in merged])
    assert actual == expected

    expected = "\nselect able, baker, charlie, delta,\n"
    merged = merger.create_merged_line(raw_query.lines)
    actual = "".join([str(line) for line in merged])
    assert actual == expected

    with pytest.raises(CannotMergeException):
        # can't merge whitespace
        _ = merger.create_merged_line(raw_query.lines[-5:-2])


def test_basic_merge(merger: LineMerger) -> None:
    source_string = """
        nullif(
            full_name,
            ''
        ) as c,
    """.strip()
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    assert len(merged_lines) == 1

    expected_string = "nullif(full_name, '') as c,"

    result = "".join(map(str, merged_lines)).strip()
    assert result == expected_string


def test_nested_merge(merger: LineMerger) -> None:
    source_string = """
    select
        a,
        nullif(
            split_part(
                full_name,
                ' ',
                2
            ),
            ''
        ) as last_name,
    """
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    expected_string = (
        "select a, nullif(split_part(full_name, ' ', 2), '') as last_name,"
    )

    result = "".join(map(str, merged_lines)).strip()
    assert result == expected_string


def test_incomplete_merge(merger: LineMerger) -> None:
    source_string = """
    select
        first_field,
        nullif(
            split_part(
                full_name,
                ' ',
                2
            ),
            ''
        ) as last_name,
        another_field,
        case
            when short
            then 1
        end,
        yet_another_field,
        and_still_another_field
    from
        my_table
    where
        some_condition is true
    """
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    result = list(map(str, merged_lines))

    expected = [
        "\n",
        "select\n",
        "    first_field,\n",
        "    nullif(split_part(full_name, ' ', 2), '') as last_name,\n",
        "    another_field,\n",
        "    case when short then 1 end,\n",
        "    yet_another_field,\n",
        "    and_still_another_field\n",
        "from my_table\n",
        "where some_condition is true\n",
    ]

    assert result == expected


def test_cte_merge(merger: LineMerger) -> None:
    source_string = """
    with
        my_cte as (
            select * from my_table
        )
    select * from my_cte
    """.strip()
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    result = list(map(str, merged_lines))

    expected = [
        "with my_cte as (select * from my_table) select * from my_cte\n",
    ]

    assert result == expected


def test_case_then_merge(merger: LineMerger) -> None:
    source_string = """
    case
        when
            some_initial_condition_is_true
        then
            some_other_condition
        else
            something_else_entirely
    end
    """
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    result = list(map(str, merged_lines))

    expected = [
        "\n",
        "case\n",
        "    when some_initial_condition_is_true\n",
        "    then some_other_condition\n",
        "    else something_else_entirely\n",
        "end\n",
    ]

    assert result == expected


def test_merge_count_window_function(merger: LineMerger) -> None:
    source_string = (
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
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    result = list(map(str, merged_lines))

    expected = [
        "count(case when a is null then 1 end) over (\n",
        "    partition by user_id, date_trunc('year', performed_at)\n",
        ") as d,\n",
    ]

    assert result == expected


def test_split_into_segments(merger: LineMerger) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_merger/test_split_into_segments.sql"
    )
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )

    top_level_segments = merger._split_into_segments(q.lines)

    assert len(top_level_segments) == 2
    assert str(top_level_segments[0][0]).startswith("select")
    assert str(top_level_segments[1][0]).startswith("from")

    select_segment = [top_level_segments[0]]

    assert select_segment == merger._split_into_segments(select_segment[0])

    select_lines = select_segment[0]
    assert not (
        select_lines[-1].closes_bracket_from_previous_line
        and select_lines[-1].depth == select_lines[0].depth
    )

    indented_segments = merger._split_into_segments(select_lines[1:])
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


def test_split_into_segments_empty(merger: LineMerger) -> None:
    no_lines: List[Line] = []
    result = merger._split_into_segments(no_lines)
    assert result == []


def test_segment_continues_operator_sequence(merger: LineMerger) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_merger/test_segment_continues_operator_sequence.sql"
    )
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )

    segments = merger._split_into_segments(q.lines)
    assert len(segments) == 8

    p2_result = [
        merger._segment_continues_operator_sequence(s, min_priority=2) for s in segments
    ]
    p2_expected = [False, True, True, False, True, False, True, True]
    assert p2_result == p2_expected

    p1_result = [
        merger._segment_continues_operator_sequence(s, min_priority=1) for s in segments
    ]
    p1_expected = [False, True, False, False, True, False, False, True]
    assert p1_result == p1_expected

    p0_result = [
        merger._segment_continues_operator_sequence(s, min_priority=0) for s in segments
    ]
    p0_expected = [False, False, False, False, True, False, False, False]
    assert p0_result == p0_expected


@pytest.mark.parametrize("p", [0, 1])
def test_segment_continues_operator_sequence_empty(merger: LineMerger, p: int) -> None:
    source_string = "\n\n\n\n"
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    result = merger._segment_continues_operator_sequence(q.lines, min_priority=p)
    assert result is True


def test_merge_single_line(merger: LineMerger) -> None:
    source_string = "select 1\n"
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    merged_lines = merger.create_merged_line(q.lines)
    assert merged_lines == q.lines


def test_merge_lines_split_by_operators(merger: LineMerger) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_merger/test_merge_lines_split_by_operators.sql"
    )
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    result_string = "".join([str(line) for line in merged_lines])
    assert result_string == expected_string


def test_merge_chained_parens(merger: LineMerger) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_merger/test_merge_chained_parens.sql"
    )
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    result_string = "".join([str(line) for line in merged_lines])
    assert result_string == expected_string


def test_merge_operators_before_children(merger: LineMerger) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_merger/test_merge_operators_before_children.sql"
    )
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    result_string = "".join([str(line) for line in merged_lines])
    assert result_string == expected_string


def test_do_not_merge_very_long_chains(merger: LineMerger) -> None:
    source_string = "a" + ("\n+ b" * 40) + "\n"
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    result_string = "".join([str(line) for line in merged_lines])

    assert result_string == source_string


def test_respect_extra_blank_lines(merger: LineMerger) -> None:
    source_string = """
    select
        one_field,
        another_field,
        yet_another_field


    from
        my_table

    join
        your_table
        on my_table.your_id
        = your_table.my_id


    where
        something is true
    """.lstrip()
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    assert merged_lines[1].is_blank_line
    assert merged_lines[2].is_blank_line
    assert merged_lines[4].is_blank_line
    assert merged_lines[6].is_blank_line
    assert merged_lines[7].is_blank_line


@pytest.mark.parametrize("sep", [";", "union", "union all", "intersect", "except"])
def test_do_not_merge_across_query_dividers(merger: LineMerger, sep: str) -> None:
    source_string = f"select 1\n{sep}\nselect2\n"
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    assert raw_query.lines == merged_lines


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
    merger: LineMerger, source_string: str, expected_result: bool
) -> None:
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    assert merger._tail_closes_head(q.lines) == expected_result


@pytest.mark.parametrize(
    "source_string,expected_idx",
    [
        ("case\nfoo\nend\n", 0),
        ("\n\n\ncount(\n*\n)", 3),
        ("\n\n\n    count(\n*\n)", 3),
        ("\n     \n\n    count(\n*\n)", 3),
    ],
)
def test_get_first_nonblank_line(
    merger: LineMerger, source_string: str, expected_idx: int
) -> None:
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    line, i = merger._get_first_nonblank_line(q.lines)
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
def test_get_first_nonblank_line_raises(merger: LineMerger, source_string: str) -> None:
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    with pytest.raises(SqlfmtSegmentError):
        _, _ = merger._get_first_nonblank_line(q.lines)


def test_maybe_stubbornly_merge(merger: LineMerger) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_merger/test_maybe_stubbornly_merge.sql"
    )
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    segments = merger._split_into_segments(q.lines)
    merged_segments = merger._maybe_stubbornly_merge(segments)
    result_string = "".join(
        [line.render_with_comments(88) for line in itertools.chain(*merged_segments)]
    )
    assert result_string == expected_string


def test_maybe_stubbornly_merge_single_segment(merger: LineMerger) -> None:
    source_string = "select\na,\nb\n"
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    segments = merger._split_into_segments(q.lines)
    assert len(segments) == 1
    merged_segments = merger._maybe_stubbornly_merge(segments)
    assert merged_segments == segments


def test_fix_standalone_operators(merger: LineMerger) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_merger/test_fix_standalone_operators.sql"
    )
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )

    # first pass shouldn't do anything
    segments = merger._split_into_segments(q.lines)
    assert len(segments) == 11
    fixed_segments = merger._fix_standalone_operators(segments)
    assert len(fixed_segments) == len(segments)

    result_string = "".join([str(line) for line in itertools.chain(*fixed_segments)])
    assert result_string == expected_string


@pytest.mark.parametrize(
    "source_string,expected_result",
    [
        ("[\noffset(\n1\n)\n]\n", True),
        ("[offset(1)]\n", True),
        ("[\nsafe_offset(1)\n]\n", True),
        ("split('abcde', 'b')[offset(1)]\n", False),
        ("my_array[ordinal(1)]\n", False),
        ("", False),
    ],
)
def test_segment_is_array_indexing(
    merger: LineMerger, source_string: str, expected_result: bool
) -> None:
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    assert merger._segment_is_array_indexing(q.lines) == expected_result
