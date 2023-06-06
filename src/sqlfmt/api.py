import asyncio
import codecs
import concurrent.futures
import locale
import sys
from functools import partial
from glob import glob
from itertools import zip_longest
from pathlib import Path, PurePath
from typing import (
    Awaitable,
    Callable,
    Collection,
    Dict,
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
from sqlfmt.exception import SqlfmtEquivalenceError, SqlfmtError, SqlfmtUnicodeError
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
    exclude_set = set()

    if mode.exclude:
        for s in mode.exclude:
            if PurePath(s).is_absolute():
                exclude_set.update([Path(g) for g in glob(s, recursive=True)])
            elif mode.exclude_root is not None:
                try:
                    exclude_set.update(mode.exclude_root.glob(s))
                except IndexError:
                    # for some reason Path.glob(".") raises an index error,
                    # although glob.glob(".") returns ["."]
                    pass
            else:
                try:
                    exclude_set.update(Path.cwd().glob(s))
                except IndexError:
                    pass

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
    Takes a list of absolute paths (files or directories) and a mode as an input, and
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
                    encoding="",
                    utf_bom="",
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
    source, encoding, utf_bom = _read_path_or_stdin(path, mode)
    try:
        formatted = format_string(source, mode)
        return SqlFormatResult(
            source_path=path,
            source_string=source,
            formatted_string=formatted,
            encoding=encoding,
            utf_bom=utf_bom,
        )
    except SqlfmtError as e:
        return SqlFormatResult(
            source_path=path,
            source_string=source,
            formatted_string="",
            encoding=encoding,
            utf_bom=utf_bom,
            exception=e,
        )


def _update_source_files(results: Iterable[SqlFormatResult]) -> None:
    """
    Overwrites file contents at result.source_path with result.formatted_string.

    No-ops for unchanged files, results without a source path, and empty files
    """
    for res in results:
        if res.has_changed and res.source_path != STDIN_PATH and res.formatted_string:
            with open(res.source_path, "w", encoding=res.encoding) as f:
                f.write(res.formatted_string)


def _read_path_or_stdin(path: Path, mode: Mode) -> Tuple[str, str, str]:
    """
    If passed a Path, calls open() and read() and returns contents as
    a tuple of strings. The first element is the contents of the file; the
    second element is the encoding used to read the file; the third
    element is either the utf BOM or an empty string.

    If passed Path("-"), calls sys.stdin.read()
    """
    encoding = (
        (
            locale.getpreferredencoding()
            if mode.encoding.lower() == "inherit"
            else mode.encoding
        )
        .lower()
        .replace("-", "_")
    )
    bom_map: Dict[str, List[bytes]] = {
        "utf": [codecs.BOM_UTF8],
        "utf8": [codecs.BOM_UTF8],
        "u8": [codecs.BOM_UTF8],
        "utf16": [codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE],
        "u16": [codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE],
        "utf16le": [codecs.BOM_UTF16_LE],
        "utf16be": [codecs.BOM_UTF16_BE],
        "utf32": [codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE],
        "u32": [codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE],
        "utf32le": [codecs.BOM_UTF32_LE],
        "utf32be": [codecs.BOM_UTF32_BE],
    }
    detected_bom = ""
    if path == STDIN_PATH:
        # todo: customize encoding of stdin
        source = sys.stdin.read()
    else:
        try:
            with open(path, "r", encoding=encoding) as f:
                source = f.read()
            if encoding.startswith("utf") and encoding != "utf_8_sig":
                for b in [
                    bom.decode(encoding)
                    for bom in bom_map.get(encoding.replace("_", ""), [])
                ]:
                    if source.startswith(b):
                        detected_bom = b
                        source = source[len(b) :]
                        break

        except UnicodeDecodeError as e:
            raise SqlfmtUnicodeError(
                f"Error reading file {path}\n"
                f"File could not be decoded using {encoding}. "
                f"Specifically, {repr(e.object)} at position {e.start} failed "
                f"with: {e.reason}.\n"
                "You can specify a different encoding by running sqlfmt "
                "with the --encoding option. Or set --encoding to 'none' to "
                "use the system default encoding. We suggest always using "
                "utf-8 for all files."
            )
    return source, encoding, detected_bom


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

    raw_comments = [
        comment.token.token for line in raw_query.lines for comment in line.comments
    ]
    result_comments = [
        comment.token.token for line in result_query.lines for comment in line.comments
    ]
    stripped_raw = "".join(
        ["".join(c.split()).replace("--", "").replace("#", "") for c in raw_comments]
    )
    stripped_res = "".join(
        ["".join(c.split()).replace("--", "").replace("#", "") for c in result_comments]
    )
    try:
        assert stripped_raw == stripped_res
    except AssertionError:
        raw_len = len(stripped_raw)
        result_len = len(stripped_res)
        mismatch_pos = 0
        mismatch_raw = ""
        mismatch_res = ""

        for i, (raw, res) in enumerate(zip_longest(stripped_raw, stripped_res)):
            if raw is not res:
                mismatch_pos = i
                mismatch_raw = stripped_raw[i : i + 25]
                mismatch_res = stripped_res[i : i + 25]
                break

        raise SqlfmtEquivalenceError(
            "There was a problem formatting your query that "
            "caused the safety check to fail. Please open an "
            f"issue. Raw query had {raw_len} comment characters; formatted "
            f"query had {result_len} comment characters. First mismatching "
            f"character at position {mismatch_pos}: raw: {mismatch_raw}; "
            f"result: {mismatch_res}."
        )
