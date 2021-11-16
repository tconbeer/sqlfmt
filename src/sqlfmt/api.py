import sys
from pathlib import Path
from typing import Iterable, Iterator, List, Set, TextIO, Union

from sqlfmt.exception import SqlfmtError
from sqlfmt.formatter import QueryFormatter
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.report import Report, SqlFormatResult


def run(files: List[str], mode: Mode) -> Report:
    """
    Runs sqlfmt on all files in list of given paths (files), using the specified mode.

    Modifies sql files in place, by default. Check or diff mode do not modify files,
    they only create a report.

    Returns a Report that can be queried or printed.
    """

    matched_paths: Set[Union[Path, TextIO]] = set()
    matched_paths.update(_generate_matched_paths([Path(s) for s in files], mode))

    results = list(_generate_results(matched_paths, mode))
    report = Report(results, mode)

    if not (mode.check or mode.diff):
        _update_source_files(results)

    return report


def _generate_results(
    paths: Iterable[Union[Path, TextIO]], mode: Mode
) -> Iterator[SqlFormatResult]:
    """
    Runs sqlfmt on all files in an iterable of given paths, using the specified mode.
    Yields SqlFormatResults.
    """
    for p in paths:

        if isinstance(p, Path):
            with open(p, "r") as f:
                source = f.read()
        else:
            # p is sys.stdin
            source = p.read()
            p = Path("STDIN")

        try:
            formatted = format_string(source, mode)
            yield SqlFormatResult(
                source_path=p, source_string=source, formatted_string=formatted
            )
        except SqlfmtError as e:
            yield SqlFormatResult(
                source_path=p,
                source_string=source,
                formatted_string="",
                exception=e,
            )


def _generate_matched_paths(
    paths: Iterable[Path], mode: Mode
) -> Iterator[Union[Path, TextIO]]:
    for p in paths:
        if str(p) == "-":
            yield sys.stdin
        elif p.is_file() and "".join(p.suffixes) in (mode.SQL_EXTENSIONS):
            yield p
        elif p.is_dir():
            yield from (_generate_matched_paths(p.iterdir(), mode))


def _update_source_files(results: Iterable[SqlFormatResult]) -> None:
    """
    Overwrites file contents at result.source_path with result.formatted_string.

    No-ops for unchanged files, results without a source path, and empty files
    """
    for res in results:
        if (
            res.has_changed
            and res.source_path != Path("STDIN")
            and res.formatted_string
        ):
            with open(res.source_path, "w") as f:
                f.write(res.formatted_string)


def format_string(source: str, mode: Mode) -> str:
    raw_query = Query.from_source(source_string=source, mode=mode)
    formatter = QueryFormatter(mode)
    formatted_query = formatter.format(raw_query)
    return str(formatted_query)
