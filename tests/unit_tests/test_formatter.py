from sqlfmt.formatter import QueryFormatter
from sqlfmt.mode import Mode


def test_dedent_jinja_block_ends(default_mode: Mode) -> None:
    formatter = QueryFormatter(default_mode)
    source_string = (
        "{% if foo %}\n"
        "select\n"
        "{% else %}\n"
        "select distinct\n"
        "    {% endif %}\n"
        "    my_col\n"
    )
    raw_query = formatter.mode.dialect.initialize_analyzer(
        formatter.mode.line_length
    ).parse_query(source_string)
    depth_before = [line.depth for line in raw_query.lines]
    assert depth_before[-2] == (1, 0)
    new_lines = formatter._dedent_jinja_blocks(raw_query.lines)
    depth_after = [line.depth for line in new_lines]
    assert depth_after <= depth_before
    assert depth_after[-2] == (0, 0)


def test_dedent_jinja_blocks(default_mode: Mode) -> None:
    formatter = QueryFormatter(default_mode)
    source_string = (
        "with\n"
        "    a as (select * from a),\n"
        "    {% for i in range(n) %}\n"
        "select\n"
        "    *\n"
        "from\n"
        "    dont_do_this_{{ i }}\n"
        "    {% if not loop.last -%}\n"
        "union all\n"
        "    {%- endif %}\n"
        "    {% endfor %}\n"
    )
    raw_query = formatter.mode.dialect.initialize_analyzer(
        formatter.mode.line_length
    ).parse_query(source_string)
    new_lines = formatter._dedent_jinja_blocks(raw_query.lines)
    jinja_depths = [
        line.depth[0] for line in new_lines if line.is_standalone_jinja_statement
    ]
    assert all([line_depth == 0 for line_depth in jinja_depths])


def test_remove_extra_blank_lines(default_mode: Mode) -> None:
    formatter = QueryFormatter(default_mode)
    source_string = (
        "select 1\n;\n\n\n\n"
        "select\n    1,\n\n\n    2\n;\n"
        "{% macro foo() %}\n\n\n\n\nfoo\n{% endmacro %}\n\n\n\n\n\n\n"
    )
    expected_string = (
        "select 1\n;\n\n\n"
        "select\n    1,\n\n    2\n;\n"
        "{% macro foo() %}\n\nfoo\n{% endmacro %}\n"
    )
    raw_query = formatter.mode.dialect.initialize_analyzer(
        formatter.mode.line_length
    ).parse_query(source_string)
    new_lines = formatter._remove_extra_blank_lines(raw_query.lines)
    assert "".join([str(line) for line in new_lines]) == expected_string
