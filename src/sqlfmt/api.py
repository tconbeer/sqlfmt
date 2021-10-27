from pathlib import Path
from typing import Iterable, Iterator, List, Set

from sqlfmt.formatter import QueryFormatter
from sqlfmt.mode import Mode
from sqlfmt.parser import Query
from sqlfmt.report import Report, SqlFormatResult
from sqlfmt.utils import display_output, gen_sql_files


def run(files: List[str], mode: Mode) -> int:
    """
    Runs sqlfmt on all files in list of given paths (files), using the specified mode.
    Returns the exit code for the cli; 0 indicates success, 1 indicates failed check,
    2 indicates unhandled exception
    """
    matched_paths: Set[Path] = set()
    matched_paths.update(gen_sql_files([Path(s) for s in files], mode))

    results = list(_generate_results(matched_paths, mode))
    report = Report(results, mode)

    display_output(str(report))

    if mode.output == "update":
        _update_source_files(results)
    elif mode.output == "check":
        if any([res.has_changed for res in results]):
            return 1
    elif mode.output == "diff":
        display_output("Diff not implemented!")
        return 2

    return 0


def _generate_results(paths: Iterable[Path], mode: Mode) -> Iterator[SqlFormatResult]:
    """
    Runs sqlfmt on all files in an iterable of given paths, using the specified mode.
    Yields SqlFormatResults.
    """
    for p in paths:
        with open(p, "r") as f:
            source = f.read()
            formatted = format_string(source, mode)
            yield SqlFormatResult(
                source_path=p, source_string=source, formatted_string=formatted
            )


def _update_source_files(results: Iterable[SqlFormatResult]) -> None:
    """
    Overwrites file contents at result.source_path with result.formatted_string.

    No-ops for unchanged files, results without a source path, and empty files
    """
    for res in results:
        if res.has_changed and res.source_path and res.formatted_string:
            with open(res.source_path, "w") as f:
                f.write(res.formatted_string)


def format_string(source: str, mode: Mode) -> str:
    raw_query = Query.from_source(source_string=source, mode=mode)
    formatter = QueryFormatter(mode)
    formatted_query = formatter.format(raw_query)
    return str(formatted_query)
