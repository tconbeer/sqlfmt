from sqlfmt.merger import LineMerger
from sqlfmt.mode import Mode
from sqlfmt.parser import Query


def test_basic_merge() -> None:
    source_string = """
        nullif(
            full_name,
            ''
        ) as c,
    """
    mode = Mode()
    raw_query = Query.from_source(source_string, mode)
    merger = LineMerger(mode)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    expected_string = "nullif(full_name, '') as c,"

    result = "".join(map(str, merged_lines)).strip()
    assert result == expected_string


def test_nested_merge() -> None:
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
    mode = Mode()
    raw_query = Query.from_source(source_string, mode)
    merger = LineMerger(mode)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    expected_string = (
        "select a, nullif(split_part(full_name, ' ', 2), '') as last_name,"
    )

    result = "".join(map(str, merged_lines)).strip()
    assert result == expected_string


def test_incomplete_merge() -> None:
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
    mode = Mode()
    raw_query = Query.from_source(source_string, mode)
    merger = LineMerger(mode)
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


def test_cte_merge() -> None:
    source_string = """
    with
        my_cte as (
            select * from my_table
        )
    select * from my_cte
    """
    mode = Mode()
    raw_query = Query.from_source(source_string, mode)
    merger = LineMerger(mode)
    merged_lines = merger.maybe_merge_lines(raw_query.lines)

    result = list(map(str, merged_lines))

    expected = [
        "\n",
        "with my_cte as (select * from my_table) select * from my_cte\n",
    ]

    assert result == expected


def test_case_then_merge() -> None:
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
    mode = Mode()
    raw_query = Query.from_source(source_string, mode)
    merger = LineMerger(mode)
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
