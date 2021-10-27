from pathlib import Path
from typing import List

import pytest

from sqlfmt.api import SqlFormatResult
from sqlfmt.mode import Mode
from sqlfmt.report import Report


@pytest.fixture
def no_change_results() -> List[SqlFormatResult]:
    results = [
        SqlFormatResult(
            source_path=Path("~/path/to/file.sql"),
            source_string="select * from my_table\n",
            formatted_string="select * from my_table\n",
        ),
        SqlFormatResult(
            source_path=Path("~/path/to/another_file.sql"),
            source_string="select * from my_table where true\n",
            formatted_string="select * from my_table where true\n",
        ),
    ]
    return results


@pytest.fixture
def changed_results() -> List[SqlFormatResult]:
    results = [
        SqlFormatResult(
            source_path=Path("~/path/to/file.sql"),
            source_string="select * from my_table\n",
            formatted_string="select * from my_table\n",
        ),
        SqlFormatResult(
            source_path=Path("~/path/to/another_file.sql"),
            source_string="SELECT * from my_table where true",
            formatted_string="select * from my_table where true\n",
        ),
        SqlFormatResult(
            source_path=Path("~/path/to/yet_another_file.sql"),
            source_string="select a,\n b\n * from my_table where \n a = b\n",
            formatted_string="select a, b from my_table where a = b\n",
        ),
    ]
    return results


def test_no_change_report(
    no_change_results: List[SqlFormatResult], default_mode: Mode
) -> None:
    report = Report(no_change_results, default_mode)
    assert report
    assert str(report) == "2 files left unchanged."


def test_no_change_verbose_report(
    no_change_results: List[SqlFormatResult], verbose_mode: Mode
) -> None:
    report = Report(no_change_results, verbose_mode)
    assert report

    expected_report = (
        "2 files left unchanged.\n"
        "~/path/to/another_file.sql left unchanged.\n"
        "~/path/to/file.sql left unchanged."
    )
    assert str(report) == expected_report


def test_changed_report_default_mode(
    changed_results: List[SqlFormatResult], default_mode: Mode
) -> None:
    report = Report(changed_results, default_mode)
    assert report
    expected_report = (
        "2 files formatted.\n"
        "1 file left unchanged.\n"
        "~/path/to/another_file.sql formatted.\n"
        "~/path/to/yet_another_file.sql formatted."
    )
    assert str(report) == expected_report


def test_changed_report_verbose_mode(
    changed_results: List[SqlFormatResult], verbose_mode: Mode
) -> None:
    report = Report(changed_results, verbose_mode)
    assert report
    expected_report = (
        "2 files formatted.\n"
        "1 file left unchanged.\n"
        "~/path/to/another_file.sql formatted.\n"
        "~/path/to/yet_another_file.sql formatted.\n"
        "~/path/to/file.sql left unchanged."
    )
    assert str(report) == expected_report


def test_changed_report_check_mode(
    changed_results: List[SqlFormatResult], check_mode: Mode
) -> None:
    report = Report(changed_results, check_mode)
    assert report
    expected_report = (
        "2 files failed formatting check.\n"
        "1 file passed formatting check.\n"
        "~/path/to/another_file.sql failed formatting check.\n"
        "~/path/to/yet_another_file.sql failed formatting check."
    )
    assert str(report) == expected_report


def test_changed_report_verbose_check_mode(
    changed_results: List[SqlFormatResult], verbose_check_mode: Mode
) -> None:
    report = Report(changed_results, verbose_check_mode)
    assert report
    expected_report = (
        "2 files failed formatting check.\n"
        "1 file passed formatting check.\n"
        "~/path/to/another_file.sql failed formatting check.\n"
        "~/path/to/yet_another_file.sql failed formatting check.\n"
        "~/path/to/file.sql passed formatting check."
    )
    assert str(report) == expected_report


def test_no_change_report_check_mode(
    no_change_results: List[SqlFormatResult], check_mode: Mode
) -> None:
    report = Report(no_change_results, check_mode)
    assert report
    assert str(report) == "2 files passed formatting check."


def test_no_change_report_diff_mode(
    no_change_results: List[SqlFormatResult], diff_mode: Mode
) -> None:
    report = Report(no_change_results, diff_mode)
    assert report
    assert str(report) == "2 files passed formatting check."


def test_changed_report_diff_mode(
    changed_results: List[SqlFormatResult], diff_mode: Mode
) -> None:
    report = Report(changed_results, diff_mode)
    expected_report = (
        "2 files failed formatting check.\n"
        "1 file passed formatting check.\n"
        "~/path/to/another_file.sql failed formatting check.\n"
        "--- source_query\n"
        "+++ formatted_query\n"
        "@@ -1 +1 @@\n"
        "-SELECT * from my_table where true\n"
        "\\ No newline at end of file\n"
        "+select * from my_table where true\n"
        "\n"
        "~/path/to/yet_another_file.sql failed formatting check.\n"
        "--- source_query\n"
        "+++ formatted_query\n"
        "@@ -1,4 +1 @@\n"
        "-select a,\n"
        "- b\n"
        "- * from my_table where \n"
        "- a = b\n"
        "+select a, b from my_table where a = b\n"
    )
    assert report
    assert str(report) == expected_report
