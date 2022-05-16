import asyncio
import concurrent.futures
import sys
from functools import partial
from glob import glob
from pathlib import Path
from typing import Callable, Collection, Iterable, List, Set, TypeVar

from sqlfmt.cache import Cache, check_cache, clear_cache, load_cache, write_cache
from sqlfmt.exception import SqlfmtError
from sqlfmt.formatter import QueryFormatter
from sqlfmt.mode import Mode
from sqlfmt.report import STDIN_PATH, Report, SqlFormatResult

T = TypeVar("T")
R = TypeVar("R")


def format_string(source_string: str, mode: Mode) -> str:
    """
    Takes a raw query string and a mode as input, returns the formatted query
    as a string, or raises a SqlfmtError if the string cannot be formatted
    """
    analyzer = mode.dialect.initialize_analyzer(line_length=mode.line_length)
    raw_query = analyzer.parse_query(source_string=source_string)
    formatter = QueryFormatter(mode)
    formatted_query = formatter.format(raw_query)
    return str(formatted_query)


def run(files: List[Path], mode: Mode) -> Report:
    """
    Runs sqlfmt on all files in list of given paths (files), using the specified mode.

    Modifies sql files in place, by default. Check or diff mode do not modify files,
    they only create a report.

    Returns a Report that can be queried or printed.
    """

    if mode.reset_cache:
        clear_cache()
        cache = {}
    else:
        cache = load_cache()

    matched_paths = _get_matching_paths(files, mode)
    results = _format_many(matched_paths, cache, mode)

    report = Report(results, mode)

    if not (mode.check or mode.diff):
        _update_source_files(results)
    write_cache(cache, results, mode)

    return report


def _get_matching_paths(paths: Iterable[Path], mode: Mode) -> Set[Path]:
    """
    Takes a list of paths (files or directories) and a mode as an input, and
    yields paths to individual files that match the input paths (or are contained in
    its directories) and are not excluded by the mode's exclude glob
    """
    include_set = _get_included_paths(paths, mode)

    if mode.exclude:
        globs = []
        for pn in mode.exclude:
            globs.extend(glob(pn, recursive=True))
        exclude_set = {Path(s) for s in globs}
    else:
        exclude_set = set()

    return include_set - exclude_set


def _get_included_paths(paths: Iterable[Path], mode: Mode) -> Set[Path]:
    """
    Takes a list of paths (files or directories) and a mode as an input, and
    yields paths to individual files that match the input paths (or are contained in
    its directories)
    """
    include_set = set()
    for p in paths:
        if p == STDIN_PATH:
            include_set.add(p)
        elif p.is_file() and "".join(p.suffixes) in (mode.SQL_EXTENSIONS):
            include_set.add(p)
        elif p.is_dir():
            include_set |= _get_included_paths(p.iterdir(), mode)

    return include_set


def _format_many(
    paths: Collection[Path], cache: Cache, mode: Mode
) -> List[SqlFormatResult]:
    """
    Runs sqlfmt on all files in a collection of paths, using the specified mode.

    If there are multiple paths and the mode allows it, uses asyncio's implementation
    of multiprocessing. Otherwise, reverts to single-processing behavior

    Returns a list of SqlFormatResults. Does not write formatted Queries back to disk
    """
    format_func = partial(_format_one, cache=cache, mode=mode)
    if len(paths) > 1 and not mode.single_process:
        results: List[SqlFormatResult] = asyncio.get_event_loop().run_until_complete(
            _multiprocess_map(format_func, paths)
        )
    else:
        results = list(map(format_func, paths))

    return results


async def _multiprocess_map(func: Callable[[T], R], seq: Iterable[T]) -> List[R]:
    """
    Using multiple processes, creates a Future for each application of func to
    an item in seq, then gathers all Futures and returns the result.

    Provides a similar interface to the map() built-in, but executes in multiple
    processes.
    """
    loop = asyncio.get_event_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        tasks = []
        for item in seq:
            tasks.append(loop.run_in_executor(pool, func, item))
        results: List[R] = await asyncio.gather(*tasks)
    return results


def _format_one(path: Path, cache: Cache, mode: Mode) -> SqlFormatResult:
    """
    Runs format_string on the contents of a single file (found at path),
    unless the cache contains a matching version of that file. Handles
    potential user errors in formatted code, and returns a SqlfmtResult
    """
    cached = check_cache(cache=cache, p=path)
    if cached:
        return SqlFormatResult(
            source_path=path, source_string="", formatted_string="", from_cache=True
        )
    else:
        source = _read_path_or_stdin(path)
        try:
            formatted = format_string(source, mode)
            return SqlFormatResult(
                source_path=path, source_string=source, formatted_string=formatted
            )
        except SqlfmtError as e:
            return SqlFormatResult(
                source_path=path,
                source_string=source,
                formatted_string="",
                exception=e,
            )


def _update_source_files(results: Iterable[SqlFormatResult]) -> None:
    """
    Overwrites file contents at result.source_path with result.formatted_string.

    No-ops for unchanged files, results without a source path, and empty files
    """
    for res in results:
        if res.has_changed and res.source_path != STDIN_PATH and res.formatted_string:
            with open(res.source_path, "w") as f:
                f.write(res.formatted_string)


def _read_path_or_stdin(path: Path) -> str:
    """
    If passed a Path, calls open() and read() and returns contents as a string.

    If passed a TextIO buffer, calls read() directly
    """
    if path == STDIN_PATH:
        source = sys.stdin.read()
    else:
        with open(path, "r") as f:
            source = f.read()
    return source
