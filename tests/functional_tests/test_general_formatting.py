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
        "unformatted/100_select_case.sql",
        "unformatted/101_multiline.sql",
        "unformatted/102_lots_of_comments.sql",
        pytest.param("unformatted/103_window_functions.sql", marks=pytest.mark.xfail),
        pytest.param("unformatted/200_base_model.sql", marks=pytest.mark.xfail),
    ],
)
def test_formatting(p: str) -> None:
    mode = Mode()

    source, expected = read_test_data(p)
    actual = format_string(source, mode)

    check_formatting(expected, actual, ctx=p)

    second_pass = format_string(actual, mode)
    check_formatting(expected, second_pass, ctx=f"2nd-{p}")
