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
        "preformatted/301_multiline_jinjafmt.sql",
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
        "unformatted/300_jinjafmt.sql",
    ],
)
def test_formatting(p: str) -> None:
    mode = Mode()

    source, expected = read_test_data(p)
    actual = format_string(source, mode)

    check_formatting(expected, actual, ctx=p)

    second_pass = format_string(actual, mode)
    check_formatting(expected, second_pass, ctx=f"2nd-{p}")
