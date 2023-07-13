import pytest

from sqlfmt.api import format_string
from sqlfmt.mode import Mode
from tests.util import check_formatting, read_test_data


@pytest.mark.parametrize(
    "p",
    [
        "preformatted/001_select_1.sql",
        "preformatted/002_select_from_where.sql",
        "preformatted/003_literals.sql",
        "preformatted/004_with_select.sql",
        "preformatted/005_fmt_off.sql",
        "preformatted/006_fmt_off_447.sql",
        "preformatted/301_multiline_jinjafmt.sql",
        "preformatted/400_create_table.sql",
        "unformatted/100_select_case.sql",
        "unformatted/101_multiline.sql",
        "unformatted/102_lots_of_comments.sql",
        "unformatted/103_window_functions.sql",
        "unformatted/104_joins.sql",
        "unformatted/106_leading_commas.sql",
        "unformatted/107_jinja_blocks.sql",
        "unformatted/108_test_block.sql",
        "unformatted/109_lateral_flatten.sql",
        "unformatted/110_other_identifiers.sql",
        "unformatted/111_chained_boolean_between.sql",
        "unformatted/112_semicolons.sql",
        "unformatted/113_utils_group_by.sql",
        "unformatted/114_unions.sql",
        "unformatted/115_select_star_except.sql",
        "unformatted/116_chained_booleans.sql",
        "unformatted/117_whitespace_in_tokens.sql",
        "unformatted/118_within_group.sql",
        "unformatted/119_psycopg_placeholders.sql",
        "unformatted/120_array_literals.sql",
        "unformatted/121_stubborn_merge_edge_cases.sql",
        "unformatted/122_values.sql",
        "unformatted/123_spark_keywords.sql",
        "unformatted/124_bq_compound_types.sql",
        "unformatted/125_numeric_constants.sql",
        "unformatted/126_blank_lines.sql",
        "unformatted/127_more_comments.sql",
        "unformatted/200_base_model.sql",
        "unformatted/201_basic_snapshot.sql",
        "unformatted/202_unpivot_macro.sql",
        "unformatted/203_gitlab_email_domain_type.sql",
        "unformatted/204_gitlab_tag_validation.sql",
        "unformatted/205_rittman_hubspot_deals.sql",
        "unformatted/206_gitlab_prep_geozone.sql",
        "unformatted/207_rittman_int_journals.sql",
        "unformatted/208_rittman_int_plan_breakout_metrics.sql",
        "unformatted/209_rittman_int_web_events_sessionized.sql",
        "unformatted/210_gitlab_gdpr_delete.sql",
        "unformatted/211_http_2019_cdn_17_20.sql",
        "unformatted/212_http_2019_cms_14_02.sql",
        "unformatted/213_gitlab_fct_sales_funnel_target.sql",
        "unformatted/214_get_unique_attributes.sql",
        "unformatted/215_gitlab_get_backup_table_command.sql",
        "unformatted/216_gitlab_zuora_revenue_revenue_contract_line_source.sql",
        "unformatted/217_dbt_unit_testing_csv.sql",
        "unformatted/218_multiple_c_comments.sql",
        "unformatted/300_jinjafmt.sql",
        "unformatted/400_create_fn_and_select.sql",
        "unformatted/401_explain_select.sql",
        "unformatted/402_delete_from_using.sql",
        "unformatted/403_grant_revoke.sql",
        "unformatted/404_create_function_pg_examples.sql",
        "unformatted/405_create_function_snowflake_examples.sql",
        "unformatted/406_create_function_bq_examples.sql",
        "unformatted/407_alter_function_pg_examples.sql",
        "unformatted/408_alter_function_snowflake_examples.sql",
        "unformatted/409_create_external_function.sql",
        "unformatted/410_create_warehouse.sql",
        "unformatted/411_create_clone.sql",
        "unformatted/900_create_view.sql",
        "unformatted/999_unsupported_ddl.sql",
    ],
)
def test_formatting(p: str) -> None:
    mode = Mode()

    source, expected = read_test_data(p)
    actual = format_string(source, mode)

    check_formatting(expected, actual, ctx=p)

    second_pass = format_string(actual, mode)
    check_formatting(expected, second_pass, ctx=f"2nd-{p}")
