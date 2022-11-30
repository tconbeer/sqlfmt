import itertools

import pytest

from sqlfmt.exception import CannotMergeException
from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.operator_precedence import OperatorPrecedence
from sqlfmt.segment import Segment, create_segments_from_lines
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
        _ = merger.create_merged_line(raw_query.lines[-6:-3])


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


def test_disallow_multiline(merger: LineMerger) -> None:
    source_string = """
        foo
        {{
            bar
        }}
    """.strip()
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    with pytest.raises(CannotMergeException):
        _ = merger.create_merged_line(raw_query.lines)


def test_segment_continues_operator_sequence(merger: LineMerger) -> None:
    source_string, _ = read_test_data(
        "unit_tests/test_merger/test_segment_continues_operator_sequence.sql"
    )
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )

    segments = create_segments_from_lines(q.lines)
    assert len(segments) == 9
    print([str(s[0]) for s in segments])

    p_ON_result = [
        merger._segment_continues_operator_sequence(
            s, max_precedence=OperatorPrecedence.ON
        )
        for s in segments
    ]
    p_ON_expected = [False, True, True, True, False, True, False, True, True]
    assert p_ON_result == p_ON_expected

    p_PRESENCE_result = [
        merger._segment_continues_operator_sequence(
            s, max_precedence=OperatorPrecedence.PRESENCE
        )
        for s in segments
    ]
    p_PRESENCE_expected = [False, True, True, False, False, True, False, False, True]
    assert p_PRESENCE_result == p_PRESENCE_expected

    p_MULTIPLICATION_result = [
        merger._segment_continues_operator_sequence(
            s, max_precedence=OperatorPrecedence.MULTIPLICATION
        )
        for s in segments
    ]
    p_MULTIPLICATION_expected = [
        False,
        False,
        True,
        False,
        False,
        True,
        False,
        False,
        False,
    ]
    assert p_MULTIPLICATION_result == p_MULTIPLICATION_expected

    p_OTHER_TIGHT_result = [
        merger._segment_continues_operator_sequence(
            s, max_precedence=OperatorPrecedence.OTHER_TIGHT
        )
        for s in segments
    ]
    p_OTHER_TIGHT_expected = [
        False,
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
    ]
    assert p_OTHER_TIGHT_result == p_OTHER_TIGHT_expected


@pytest.mark.parametrize("p", OperatorPrecedence.tiers())
def test_segment_continues_operator_sequence_empty(
    merger: LineMerger, p: OperatorPrecedence
) -> None:
    source_string = "\n\n\n\n"
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    result = merger._segment_continues_operator_sequence(
        Segment(q.lines), max_precedence=p
    )
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


def test_maybe_merge_blank_lines(merger: LineMerger) -> None:
    source_string = "select\n\n\n\n\n\n\n\n\n\n\n\n1\n"
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    blank_lines = raw_query.lines[1:-1]
    assert all(line.is_blank_line for line in blank_lines)
    merged_lines = merger.maybe_merge_lines(blank_lines)
    assert merged_lines == blank_lines


def test_stubborn_merge_blank_lines(merger: LineMerger) -> None:
    source_string = "a\n\n\n\n\n\n\n\n\n\n\n\nb\n"
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    prev_segment = Segment(raw_query.lines[:1])
    blank_segment = Segment(raw_query.lines[1:-1])
    assert all(line.is_blank_line for line in blank_segment)
    new_segments = merger._stubbornly_merge(
        prev_segments=[prev_segment], segment=blank_segment
    )
    assert new_segments == [prev_segment, blank_segment]


@pytest.mark.parametrize("sep", [";", "union", "union all", "intersect", "except"])
def test_do_not_merge_across_query_dividers(merger: LineMerger, sep: str) -> None:
    source_string = f"select 1\n{sep}\nselect2\n"
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    assert raw_query.lines == merged_lines


def test_maybe_stubbornly_merge(merger: LineMerger) -> None:
    source_string, expected_string = read_test_data(
        "unit_tests/test_merger/test_maybe_stubbornly_merge.sql"
    )
    q = merger.mode.dialect.initialize_analyzer(merger.mode.line_length).parse_query(
        source_string
    )
    segments = create_segments_from_lines(q.lines)
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
    segments = create_segments_from_lines(q.lines)
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
    segments = create_segments_from_lines(q.lines)
    assert len(segments) == 11
    fixed_segments = merger._fix_standalone_operators(segments)
    assert len(fixed_segments) == len(segments)

    result_string = "".join([str(line) for line in itertools.chain(*fixed_segments)])
    assert result_string == expected_string
