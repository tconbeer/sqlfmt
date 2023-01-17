import asyncio
import concurrent.futures
import sys
from functools import partial
from glob import glob
from itertools import zip_longest
from pathlib import Path
from typing import (
    Awaitable,
    Callable,
    Collection,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from tqdm import tqdm

from sqlfmt.analyzer import Analyzer
from sqlfmt.cache import Cache, check_cache, clear_cache, load_cache, write_cache
from sqlfmt.exception import SqlfmtEquivalenceError, SqlfmtError
from sqlfmt.formatter import QueryFormatter
from sqlfmt.mode import Mode as Mode
from sqlfmt.query import Query
from sqlfmt.report import STDIN_PATH, Report, SqlFormatResult

T = TypeVar("T")
R = TypeVar("R")


def format_string(source_string: str, mode: Mode) -> str:
    """
    Takes a raw query string and a mode as input, returns the formatted query
    as a string, or raises a SqlfmtError if the string cannot be formatted.

    If mode.fast is False, also performs a safety check to ensure no tokens
    are dropped from the original input.
    """
    analyzer = mode.dialect.initialize_analyzer(line_length=mode.line_length)
    raw_query = analyzer.parse_query(source_string=source_string)
    formatter = QueryFormatter(mode)
    formatted_query = formatter.format(raw_query)
    result = str(formatted_query)

    if not mode.fast and not mode.check and not mode.diff:
        _perform_safety_check(analyzer, raw_query, result)

    return result


def run(
    files: Collection[Path],
    mode: Mode,
    callback: Optional[Callable[[Awaitable[SqlFormatResult]], None]] = None,
) -> Report:
    """
    Runs sqlfmt on all files in Collection of Paths (files), using the specified Mode.

    Modifies sql files in place, by default. Check or diff Mode do not modify files,
    they only create a Report.

    If a callback is provided, will execute the callback after each file is formatted.

    Returns a Report that can be queried or printed.
    """

    if mode.reset_cache:
        clear_cache()
        cache = {}
    else:
        cache = load_cache()

    results = _format_many(files, cache, mode, callback=callback)

    report = Report(results, mode)

    if not (mode.check or mode.diff):
        _update_source_files(results)
    write_cache(cache, results, mode)

    return report


def get_matching_paths(paths: Iterable[Path], mode: Mode) -> Set[Path]:
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


def initialize_progress_bar(
    total: int, mode: Mode, force_progress_bar: bool = False
) -> Tuple[tqdm, Callable[[Awaitable[SqlFormatResult]], None]]:
    """
    Return a callable that can be used with api.run to display a progress bar
    that updates after each file is formatted.

    Pass force_progress_bar to enable the progress bar, even on non-TTY
    terminals (this is handy for testing the progress bar).
    """
    if mode.no_progressbar:
        disable = True
    elif force_progress_bar:
        disable = False
    else:
        # will be disabled on non-TTY envs, enabled otherwise
        disable = None
    progress_bar: tqdm = tqdm(
        total=total, leave=False, disable=disable, delay=0.5, unit="file"
    )

    def progress_callback(_: Awaitable[SqlFormatResult]) -> None:
        progress_bar.update()

    return progress_bar, progress_callback


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
        elif p.is_file() and str(p).endswith(tuple(mode.SQL_EXTENSIONS)):
            include_set.add(p)
        elif p.is_dir():
            include_set |= _get_included_paths(p.iterdir(), mode)

    return include_set


def _format_many(
    paths: Collection[Path],
    cache: Cache,
    mode: Mode,
    callback: Optional[Callable[[Awaitable[SqlFormatResult]], None]] = None,
) -> List[SqlFormatResult]:
    """
    Runs sqlfmt on all files in a collection of paths, using the specified mode.

    If there are multiple paths and the mode allows it, uses asyncio's implementation
    of multiprocessing. Otherwise, reverts to single-processing behavior

    Returns a list of SqlFormatResults. Does not write formatted Queries back to disk
    """
    results: List[SqlFormatResult] = []
    cache_misses: List[Path] = []
    for path in paths:
        cached = check_cache(cache=cache, p=path)
        if cached:
            results.append(
                SqlFormatResult(
                    source_path=path,
                    source_string="",
                    formatted_string="",
                    from_cache=True,
                )
            )
        else:
            cache_misses.append(path)

    format_func = partial(_format_one, mode=mode)
    if len(cache_misses) > 1 and not mode.single_process:
        results.extend(
            asyncio.run(_multiprocess_map(format_func, paths, callback=callback))
        )
    else:
        results.extend((map(format_func, cache_misses)))

    return results


async def _multiprocess_map(
    func: Callable[[T], R],
    seq: Iterable[T],
    callback: Optional[Callable[[Awaitable[R]], None]] = None,
) -> List[R]:
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
            future = loop.run_in_executor(pool, func, item)
            if callback:
                future.add_done_callback(callback)
            tasks.append(future)
        results: List[R] = await asyncio.gather(*tasks)
    return results


def _format_one(path: Path, mode: Mode) -> SqlFormatResult:
    """
    Runs format_string on the contents of a single file (found at path). Handles
    potential user errors in formatted code, and returns a SqlfmtResult
    """
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

    If passed Path("-"), calls sys.stdin.read()
    """
    if path == STDIN_PATH:
        source = sys.stdin.read()
    else:
        with open(path, "r") as f:
            source = f.read()
    return source


def _perform_safety_check(analyzer: Analyzer, raw_query: Query, result: str) -> None:
    """
    Raises a SqlfmtEquivalenceError if re-lexing
    the result produces a different set of tokens than
    the original.
    """
    result_query = analyzer.parse_query(source_string=result)
    filtered_raw_tokens = [
        token.type for token in raw_query.tokens if token.type.is_equivalent_in_output
    ]
    filtered_result_tokens = [
        token.type
        for token in result_query.tokens
        if token.type.is_equivalent_in_output
    ]

    try:
        assert filtered_raw_tokens == filtered_result_tokens
    except AssertionError:
        raw_len = len(filtered_raw_tokens)
        result_len = len(filtered_result_tokens)
        mismatch_pos = 0
        mismatch_raw = ""
        mismatch_res = ""

        for i, (raw, res) in enumerate(
            zip_longest(filtered_raw_tokens, filtered_result_tokens)
        ):
            if raw is not res:
                mismatch_pos = i
                mismatch_raw = str(raw)
                mismatch_res = str(res)
                break

        raise SqlfmtEquivalenceError(
            "There was a problem formatting your query that "
            "caused the safety check to fail. Please open an "
            f"issue. Raw query was {raw_len} tokens; formatted "
            f"query was {result_len} tokens. First mismatching "
            f"token at position {mismatch_pos}: raw: {mismatch_raw}; "
            f"result: {mismatch_res}."
        )
