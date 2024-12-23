import codecs
import io
import os
from pathlib import Path
from typing import Any, List, Set, Type

import pytest
from sqlfmt.api import (
    _format_many,
    _perform_safety_check,
    _read_path_or_stdin,
    _update_source_files,
    format_markdown_string,
    format_string,
    get_matching_paths,
    initialize_progress_bar,
    run,
)
from sqlfmt.exception import (
    SqlfmtBracketError,
    SqlfmtEquivalenceError,
    SqlfmtError,
    SqlfmtUnicodeError,
)
from sqlfmt.mode import Mode
from tqdm import tqdm


@pytest.fixture
def preformatted_files(preformatted_dir: Path) -> List[Path]:
    return list(preformatted_dir.iterdir())


@pytest.fixture
def unformatted_files(unformatted_dir: Path) -> List[Path]:
    return list(unformatted_dir.iterdir())


@pytest.fixture
def file_discovery_dir() -> Path:
    return Path("tests/data/unit_tests/test_api/test_file_discovery").resolve()


@pytest.fixture
def all_files(file_discovery_dir: Path) -> Set[Path]:
    p = file_discovery_dir
    files = {
        p / "top_level_file.sql",
        p / "top_level_file.two.sql",
        p / "top_level_markdown_file.md",
        p / "a_directory/one_file.sql",
        p / "a_directory/one_markdown_file.md",
        p / "a_directory/nested_directory/another_file.sql",
        p / "a_directory/nested_directory/another_markdown_file.md",
        p / "a_directory/nested_directory/j2_extension.sql.jinja",
        p / "a_directory/symlink_source_directory/symlink_file.sql",
        p / "a_directory/symlink_target_directory/symlink_file.sql",
    }
    return files


@pytest.fixture
def sql_jinja_files(file_discovery_dir: Path) -> Set[Path]:
    p = file_discovery_dir
    files = {p / "a_directory/nested_directory/j2_extension.sql.jinja"}
    return files


def test_file_discovery(
    default_mode: Mode, file_discovery_dir: Path, all_files: Set[Path]
) -> None:
    res = get_matching_paths(file_discovery_dir.iterdir(), default_mode)

    assert res == all_files


@pytest.mark.parametrize(
    "exclude",
    [
        ["**/*_file*"],
        ["**/*.sql", "**/*.md"],
        [
            "**/top*",
            "**/a_directory/*",
            "**/a_directory/**/another_file.sql",
            "**/a_directory/**/another_markdown_file.md",
            "**/a_directory/**/symlink_file.sql",
        ],
    ],
)
def test_file_discovery_with_excludes(
    exclude: List[str], file_discovery_dir: Path, sql_jinja_files: Set[Path]
) -> None:
    mode = Mode(exclude=exclude, exclude_root=file_discovery_dir)
    res = get_matching_paths(file_discovery_dir.iterdir(), mode)
    assert res == sql_jinja_files


def test_file_discovery_with_abs_excludes(
    file_discovery_dir: Path, sql_jinja_files: Set[Path]
) -> None:
    exclude = [
        str(file_discovery_dir / "**/*.sql"),
        str(file_discovery_dir / "**/*.md"),
    ]
    mode = Mode(exclude=exclude, exclude_root=None)
    res = get_matching_paths(file_discovery_dir.iterdir(), mode)
    assert res == sql_jinja_files


def test_file_discovery_with_invalid_excludes(
    file_discovery_dir: Path, all_files: Set[Path]
) -> None:
    exclude = ["."]
    for root in [file_discovery_dir, None]:
        mode = Mode(exclude=exclude, exclude_root=root)
        res = get_matching_paths(file_discovery_dir.iterdir(), mode)
        assert res == all_files


def test_file_discovery_with_excludes_no_root(
    file_discovery_dir: Path, all_files: Set[Path], sql_jinja_files: Set[Path]
) -> None:
    mode = Mode(exclude=["**/*.sql", "**/*.md"], exclude_root=None)

    # relative to here, excludes shouldn't do anything.
    cwd = os.getcwd()
    try:
        os.chdir(Path(__file__).parent)
        res = get_matching_paths(file_discovery_dir.iterdir(), mode)
    finally:
        os.chdir(cwd)

    assert res == all_files

    # relative to file_discovery_dir, excludes should knock out most files
    try:
        os.chdir(file_discovery_dir)
        res = get_matching_paths(file_discovery_dir.iterdir(), mode)
    finally:
        os.chdir(cwd)

    assert res == sql_jinja_files


def test_format_empty_string(all_output_modes: Mode) -> None:
    source = expected = ""
    actual = format_string(source, all_output_modes)
    assert expected == actual


def test_format_markdown_empty_string(all_output_modes: Mode) -> None:
    source = expected = ""
    actual = format_markdown_string(source, all_output_modes)
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


def test_run_no_markdownfmt_mode(unformatted_files: List[Path]) -> None:
    unformatted_markdown_files = [
        file for file in unformatted_files if file.suffix == ".md"
    ]
    mode = Mode(no_markdownfmt=True)
    report = run(files=unformatted_markdown_files, mode=mode)
    assert report.number_changed == 0
    assert report.number_unchanged == len(unformatted_markdown_files)
    assert report.number_errored == 0
    assert not any([res.from_cache for res in report.results])


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

    with pytest.raises(SqlfmtEquivalenceError) as excinfo:
        # adds a comment
        _perform_safety_check(
            analyzer, raw_query, "select\n-- new comment\n    1, 2, 3\n"
        )

    assert (
        "Raw query had 0 comment characters; formatted query had 10 comment characters"
        in str(excinfo.value)
    )

    # does not raise
    _perform_safety_check(analyzer, raw_query, "select\n    1, 2, 3\n")


@pytest.mark.parametrize(
    "encoding,bom",
    [
        ("utf-8", b""),
        ("utf-8", codecs.BOM_UTF8),
        ("utf-8-sig", b""),  # encoding with utf-8-sig will add a bom
        ("utf-16", b""),
        ("utf_16_be", codecs.BOM_UTF16_BE),
        ("utf_16_le", codecs.BOM_UTF16_LE),
        ("utf-32", b""),
        ("utf_32_be", codecs.BOM_UTF32_BE),
        ("utf_32_le", codecs.BOM_UTF32_LE),
        ("cp1250", b""),
        ("cp1252", b""),
        ("latin-1", b""),
        ("ascii", b""),
    ],
)
def test_read_path_or_stdin_many_encodings(
    encoding: str, bom: bytes, tmp_path: Path
) -> None:
    p = tmp_path / "q.sql"
    # create a new file with the specified encoding and BOM
    raw_query = "select\n\n\n1\n"
    file_contents = bom + raw_query.encode(encoding)
    with open(p, "wb") as f:
        f.write(file_contents)

    mode = Mode(encoding=encoding)
    actual_source, actual_encoding, actual_bom = _read_path_or_stdin(p, mode)
    assert actual_source == raw_query
    assert actual_encoding == encoding.lower().replace("-", "_")
    assert actual_bom == bom.decode(encoding)


def test_read_path_or_stdin_error(tmp_path: Path) -> None:
    p = tmp_path / "q.sql"
    with open(p, "w", encoding="utf-8") as f:
        f.write("select 'ň' as ch")

    mode = Mode(encoding="cp1250")
    with pytest.raises(SqlfmtUnicodeError) as exc_info:
        _, _, _ = _read_path_or_stdin(p, mode)

    assert "cp1250" in str(exc_info.value)
