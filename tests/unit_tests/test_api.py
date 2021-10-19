import os
from pathlib import Path
from typing import List

import pytest

from sqlfmt.api import _generate_results, _update_source_files, format_string
from sqlfmt.mode import Mode
from tests.util import copy_test_data_to_tmp


@pytest.fixture
def mode() -> Mode:
    return Mode()


def test_format_empty_string(mode: Mode) -> None:
    source = expected = ""
    actual = format_string(source, mode)
    assert expected == actual


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


def test_generate_results_preformatted(
    preformatted_files: List[Path], mode: Mode
) -> None:
    results = list(_generate_results(preformatted_files, mode))

    assert len(results) == len(
        preformatted_files
    ), "Did not generate one result for each input file"
    assert not any([res.has_changed for res in results]), "Changed preformatted file"
    assert all(
        [raw == res.source_path for raw, res in zip(preformatted_files, results)]
    ), "Result stored a source path that doesn't match the raw path passed to api"


def test_generate_results_unformatted(
    unformatted_files: List[Path], mode: Mode
) -> None:
    results = list(_generate_results(unformatted_files, mode))

    assert len(results) == len(
        unformatted_files
    ), "Did not generate one result for each input file"
    assert all([res.has_changed for res in results]), "Did not change unformatted file"
    assert all(
        [raw == res.source_path for raw, res in zip(unformatted_files, results)]
    ), "Result stored a source path that doesn't match the raw path passed to api"


def test_update_source_files_preformatted(
    preformatted_files: List[Path], mode: Mode
) -> None:
    results = list(_generate_results(preformatted_files, mode))

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
    unformatted_files: List[Path], mode: Mode
) -> None:
    results = list(_generate_results(unformatted_files, mode))

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
