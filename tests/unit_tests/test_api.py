import io
import os
from pathlib import Path
from typing import Any, List, Type

import pytest
from tqdm import tqdm

from sqlfmt.api import (
    _format_many,
    _perform_safety_check,
    _update_source_files,
    format_string,
    get_matching_paths,
    initialize_progress_bar,
    run,
)
from sqlfmt.exception import SqlfmtBracketError, SqlfmtEquivalenceError, SqlfmtError
from sqlfmt.mode import Mode


@pytest.fixture
def preformatted_files(preformatted_dir: Path) -> List[Path]:
    return list(preformatted_dir.iterdir())


@pytest.fixture
def unformatted_files(unformatted_dir: Path) -> List[Path]:
    return list(unformatted_dir.iterdir())


def test_file_discovery(default_mode: Mode) -> None:
    p = Path("tests/data/unit_tests/test_api/test_file_discovery")
    res = list(get_matching_paths(p.iterdir(), default_mode))

    expected = (
        p / "top_level_file.sql",
        p / "top_level_file.two.sql",
        p / "a_directory/one_file.sql",
        p / "a_directory/nested_directory/another_file.sql",
        p / "a_directory/nested_directory/j2_extension.sql.jinja",
    )

    for p in expected:
        assert p in res


@pytest.mark.parametrize(
    "exclude",
    [
        ["**/*_file*"],
        ["**/*.sql"],
        ["**/top*", "**/a_directory/*", "**/a_directory/**/another_file.sql"],
    ],
)
def test_file_discovery_with_excludes(exclude: List[str]) -> None:
    mode = Mode(exclude=exclude)
    p = Path("tests/data/unit_tests/test_api/test_file_discovery")
    res = get_matching_paths(p.iterdir(), mode)

    expected = {
        # p / "top_level_file.sql",
        # p / "a_directory/one_file.sql",
        # p / "a_directory/nested_directory/another_file.sql",
        p
        / "a_directory/nested_directory/j2_extension.sql.jinja",
    }

    assert res & expected == expected


def test_format_empty_string(all_output_modes: Mode) -> None:
    source = expected = ""
    actual = format_string(source, all_output_modes)
    assert expected == actual


@pytest.mark.parametrize(
    "source,exception",
    [
        ("select )\n", SqlfmtBracketError),
        ("{{\n", SqlfmtBracketError),
    ],
)
def test_format_bad_string(
    all_output_modes: Mode, source: str, exception: Type[SqlfmtError]
) -> None:
    with pytest.raises(exception):
        _ = format_string(source, all_output_modes)


def test_format_many_preformatted(
    preformatted_files: List[Path], all_output_modes: Mode
) -> None:
    results = list(_format_many(preformatted_files, {}, all_output_modes))

    assert len(results) == len(
        preformatted_files
    ), "Did not generate one result for each input file"
    assert not any([res.has_changed for res in results]), "Changed preformatted file"
    assert all(
        [raw == res.source_path for raw, res in zip(preformatted_files, results)]
    ), "Result stored a source path that doesn't match the raw path passed to api"


def test_format_many_unformatted(
    unformatted_files: List[Path], default_mode: Mode
) -> None:
    results = list(_format_many(unformatted_files, {}, default_mode))

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
    results = list(_format_many(preformatted_files, {}, default_mode))

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
    results = list(_format_many(unformatted_files, {}, default_mode))

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
    files = get_matching_paths([unformatted_dir], default_mode)
    # confirm that we call the _update_source function
    monkeypatch.delattr("sqlfmt.api._update_source_files")
    with pytest.raises(NameError):
        _ = run(files=files, mode=default_mode)


def test_run_preformatted(
    preformatted_files: List[Path], all_output_modes: Mode, reset_cache_mode: Mode
) -> None:
    files = preformatted_files
    report = run(files=files, mode=all_output_modes)
    assert report.number_changed == 0
    assert report.number_unchanged == len(preformatted_files)
    assert report.number_errored == 0
    assert not any([res.from_cache for res in report.results])

    cached_run = run(files=files, mode=all_output_modes)
    assert cached_run.number_changed == report.number_changed
    assert cached_run.number_unchanged == report.number_unchanged
    assert cached_run.number_errored == report.number_errored
    assert all([res.from_cache for res in cached_run.results])

    uncached_run = run(files=files, mode=reset_cache_mode)
    assert uncached_run.number_changed == report.number_changed
    assert uncached_run.number_unchanged == report.number_unchanged
    assert uncached_run.number_errored == report.number_errored
    assert not any([res.from_cache for res in uncached_run.results])


def test_run_unformatted(unformatted_files: List[Path], all_output_modes: Mode) -> None:
    files = unformatted_files
    report = run(files=files, mode=all_output_modes)
    assert report.number_changed == len(unformatted_files)
    assert report.number_unchanged == 0
    assert report.number_errored == 0
    assert not any([res.from_cache for res in report.results])

    cached_run = run(files=files, mode=all_output_modes)
    if all_output_modes.diff or all_output_modes.check:
        assert cached_run.number_changed == report.number_changed
        assert cached_run.number_unchanged == report.number_unchanged
    else:
        assert cached_run.number_changed == 0
        assert cached_run.number_unchanged == report.number_changed
    assert cached_run.number_errored == report.number_errored
    if not all_output_modes.diff and not all_output_modes.check:
        assert all([res.from_cache for res in cached_run.results])


def test_run_error(error_dir: Path, all_output_modes: Mode) -> None:
    p = [error_dir]
    files = get_matching_paths(p, all_output_modes)
    report = run(files=files, mode=all_output_modes)
    assert report.number_changed == 0
    assert report.number_unchanged == 0
    assert report.number_errored == 4
    assert not any([res.from_cache for res in report.results])

    cached_run = run(files=files, mode=all_output_modes)
    assert cached_run.number_changed == report.number_changed
    assert cached_run.number_unchanged == report.number_unchanged
    assert cached_run.number_errored == report.number_errored
    assert not any([res.from_cache for res in cached_run.results])


def test_run_stdin(all_output_modes: Mode, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("select\n    1"))
    report = run(files=[Path("-")], mode=all_output_modes)
    assert report.number_changed == 1
    assert report.number_unchanged == 0
    assert report.number_errored == 0


def test_run_on_nothing(all_output_modes: Mode) -> None:
    report = run(files=[], mode=all_output_modes)
    assert report.number_changed == 0
    assert report.number_unchanged == 0
    assert report.number_errored == 0


def test_run_single_process_does_not_use_multiprocessing(
    unformatted_dir: Path, single_process_mode: Mode, monkeypatch: pytest.MonkeyPatch
) -> None:
    # confirm that we do not call _multiprocess_map; if we do,
    # this will raise
    files = get_matching_paths([unformatted_dir], single_process_mode)
    monkeypatch.delattr("sqlfmt.api._multiprocess_map")
    _ = run(files=files, mode=single_process_mode)


def test_run_with_callback(
    capsys: Any, unformatted_dir: Path, default_mode: Mode
) -> None:
    def print_dot(_: Any) -> None:
        print(".", end="", flush=True)

    files = get_matching_paths([unformatted_dir], default_mode)
    expected_dots = len(files)

    _ = run(files=files, mode=default_mode, callback=print_dot)
    captured = capsys.readouterr()

    assert "." * expected_dots in captured.out


def test_initialize_progress_bar(default_mode: Mode) -> None:
    total = 100
    progress_bar, progress_callback = initialize_progress_bar(
        total=total, mode=default_mode, force_progress_bar=True
    )
    assert progress_bar
    assert isinstance(progress_bar, tqdm)
    assert progress_bar.format_dict.get("n") == 0
    assert progress_bar.format_dict.get("total") == total

    assert progress_callback is not None
    progress_callback("foo")  # type: ignore
    assert progress_bar.format_dict.get("n") == 1


def test_initialize_disabled_progress_bar(no_progressbar_mode: Mode) -> None:
    total = 100
    progress_bar, progress_callback = initialize_progress_bar(
        total=total, mode=no_progressbar_mode, force_progress_bar=True
    )
    # a disabled progress bar's elapsed timer will not count up,
    # and calling update() will not increment n
    assert progress_bar
    assert isinstance(progress_bar, tqdm)
    assert progress_bar.format_dict.get("n") == 0
    assert progress_bar.format_dict.get("total") == total
    assert progress_bar.format_dict.get("elapsed") == 0

    assert progress_callback is not None
    progress_callback("foo")  # type: ignore
    assert progress_bar.format_dict.get("n") == 0


def test_perform_safety_check(default_mode: Mode) -> None:
    source_string = "select 1, 2, 3\n"

    analyzer = default_mode.dialect.initialize_analyzer(
        line_length=default_mode.line_length
    )
    raw_query = analyzer.parse_query(source_string)

    with pytest.raises(SqlfmtEquivalenceError) as excinfo:
        # drops last token
        _perform_safety_check(analyzer, raw_query, "select 1, 2, \n")

    assert "Raw query was 6 tokens; formatted query was 5 tokens." in str(excinfo.value)

    with pytest.raises(SqlfmtEquivalenceError) as excinfo:
        # changes a token
        _perform_safety_check(analyzer, raw_query, "select a, 2, 3\n")

    assert (
        "First mismatching token at position 1: raw: TokenType.NUMBER; "
        "result: TokenType.NAME." in str(excinfo.value)
    )

    # does not raise
    _perform_safety_check(analyzer, raw_query, "select\n    1, 2, 3\n")
    _perform_safety_check(analyzer, raw_query, "select\n-- new comment\n    1, 2, 3\n")
