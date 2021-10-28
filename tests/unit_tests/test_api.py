import os
from pathlib import Path
from typing import List, Type

import pytest

from sqlfmt.api import _generate_results, _update_source_files, format_string, run
from sqlfmt.dialect import SqlfmtParsingError
from sqlfmt.exception import SqlfmtError
from sqlfmt.line import SqlfmtBracketError
from sqlfmt.mode import Mode
from sqlfmt.parser import SqlfmtMultilineError
from tests.util import copy_test_data_to_tmp


@pytest.fixture
def preformatted_dir(tmp_path: Path) -> Path:
    """
    Copies the directory of preformatted sql files from the test/data
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["preformatted"], tmp_path)
    return test_dir


@pytest.fixture
def preformatted_files(preformatted_dir: Path) -> List[Path]:
    return list(preformatted_dir.iterdir())


@pytest.fixture
def unformatted_dir(tmp_path: Path) -> Path:
    """
    Copies the directory of unformatted sql files from the test/data
    directory into a temp directory (provided by pytest fixture tmp_path),
    and then returns the path to the temp directory.
    """
    test_dir = copy_test_data_to_tmp(["unformatted"], tmp_path)
    return test_dir


@pytest.fixture
def unformatted_files(unformatted_dir: Path) -> List[Path]:
    return list(unformatted_dir.iterdir())


@pytest.fixture
def error_dir(tmp_path: Path) -> Path:
    test_dir = copy_test_data_to_tmp(["errors"], tmp_path)
    return test_dir


def test_format_empty_string(all_output_modes: Mode) -> None:
    source = expected = ""
    actual = format_string(source, all_output_modes)
    assert expected == actual


@pytest.mark.parametrize(
    "source,exception",
    [
        ("?\n", SqlfmtParsingError),
        ("select )\n", SqlfmtBracketError),
        ("{{\n", SqlfmtMultilineError),
    ],
)
def test_format_bad_string(
    all_output_modes: Mode, source: str, exception: Type[SqlfmtError]
) -> None:
    with pytest.raises(exception):
        _ = format_string(source, all_output_modes)


def test_generate_results_preformatted(
    preformatted_files: List[Path], all_output_modes: Mode
) -> None:
    results = list(_generate_results(preformatted_files, all_output_modes))

    assert len(results) == len(
        preformatted_files
    ), "Did not generate one result for each input file"
    assert not any([res.has_changed for res in results]), "Changed preformatted file"
    assert all(
        [raw == res.source_path for raw, res in zip(preformatted_files, results)]
    ), "Result stored a source path that doesn't match the raw path passed to api"


def test_generate_results_unformatted(
    unformatted_files: List[Path], all_output_modes: Mode
) -> None:
    results = list(_generate_results(unformatted_files, all_output_modes))

    assert len(results) == len(
        unformatted_files
    ), "Did not generate one result for each input file"
    assert all([res.has_changed for res in results]), "Did not change unformatted file"
    assert all(
        [raw == res.source_path for raw, res in zip(unformatted_files, results)]
    ), "Result stored a source path that doesn't match the raw path passed to api"


def test_update_source_files_preformatted(
    preformatted_files: List[Path], default_mode: Mode
) -> None:
    results = list(_generate_results(preformatted_files, default_mode))

    expected_last_update_timestamps = [
        os.stat(res.source_path).st_mtime for res in results if res.source_path
    ]

    assert len(results) == len(expected_last_update_timestamps)

    _update_source_files(results)

    actual_last_update_timestamps = [
        os.stat(res.source_path).st_mtime for res in results if res.source_path
    ]

    assert len(expected_last_update_timestamps) == len(actual_last_update_timestamps)

    assert all(
        [
            expected == actual
            for expected, actual in zip(
                expected_last_update_timestamps, actual_last_update_timestamps
            )
        ]
    ), "Should not have written a new file for an unchanged result"


def test_update_source_files_unformatted(
    unformatted_files: List[Path], default_mode: Mode
) -> None:
    results = list(_generate_results(unformatted_files, default_mode))

    original_update_timestamps = [
        os.stat(res.source_path).st_mtime for res in results if res.source_path
    ]

    assert len(results) == len(original_update_timestamps)

    _update_source_files(results)

    new_update_timestamps = [
        os.stat(res.source_path).st_mtime for res in results if res.source_path
    ]

    assert len(new_update_timestamps) == len(original_update_timestamps)

    assert all(
        [
            new > original
            for original, new in zip(original_update_timestamps, new_update_timestamps)
        ]
    ), "Should have written a new file for an unchanged result"

    for res in results:
        assert res.source_path
        with open(res.source_path, "r") as f:
            new_file_contents = f.read()
        assert new_file_contents == res.formatted_string
        assert new_file_contents != res.source_string


def test_run_unformatted_update(
    unformatted_dir: Path, default_mode: Mode, monkeypatch: pytest.MonkeyPatch
) -> None:

    # confirm that we call the _update_source function
    monkeypatch.delattr("sqlfmt.api._update_source_files")
    with pytest.raises(NameError):
        _ = run(files=[str(unformatted_dir)], mode=default_mode)


def test_run_preformatted_check(
    preformatted_files: List[Path], check_mode: Mode
) -> None:
    exit_code = run(files=[str(f) for f in preformatted_files], mode=check_mode)
    assert exit_code == 0


def test_run_unformatted_check(unformatted_files: List[Path], check_mode: Mode) -> None:
    exit_code = run(files=[str(f) for f in unformatted_files], mode=check_mode)
    assert exit_code == 1


def test_run_unformatted_diff(unformatted_files: List[Path], diff_mode: Mode) -> None:
    exit_code = run(files=[str(f) for f in unformatted_files], mode=diff_mode)
    assert exit_code == 1


def test_run_error(error_dir: Path, all_output_modes: Mode) -> None:
    exit_code = run(files=[str(error_dir)], mode=all_output_modes)
    assert exit_code == 2
