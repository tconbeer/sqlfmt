import pytest

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
        "            a is null\n"
        "        then\n"
        "            1\n"
        "    end\n"
        ") over (\n"
        "    partition by\n"
        "        user_id,\n"
        "        date_trunc('year', performed_at)\n"
        ") as d,\n"
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
    assert len(indented_segments) == 13


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


def test_do_not_merge_across_semicolons(merger: LineMerger) -> None:
    source_string = "select 1\n;\nselect2\n"
    raw_query = merger.mode.dialect.initialize_analyzer(
        merger.mode.line_length
    ).parse_query(source_string)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)
    assert raw_query.lines == merged_lines
