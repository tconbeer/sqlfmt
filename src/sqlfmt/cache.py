import pickle
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from platformdirs import user_cache_dir

from sqlfmt.mode import Mode
from sqlfmt.report import STDIN_PATH, SqlFormatResult

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata

Cache = Dict[Path, Tuple[float, int]]


def get_cache_file() -> Path:
    """
    Returns the path to the cache file on disk
    """
    sqlfmt_version = metadata.version("shandy-sqlfmt")
    cache_dir = Path(user_cache_dir(appname="sqlfmt"))
    cache_file = cache_dir / f"cache-{sqlfmt_version}.pickle"
    return cache_file


def load_cache() -> Cache:
    """
    Returns a Cache (a dictionary keyed by file path) by loading
    from a pickle saved to disk
    """
    cache_file = get_cache_file()
    try:
        with cache_file.open("rb") as f:
            cache: Cache = pickle.load(f)
            return cache
    except (pickle.UnpicklingError, ValueError, IndexError, FileNotFoundError):
        return {}


def check_cache(cache: Cache, p: Path) -> bool:
    """
    Returns True if the path is in the cache and the cached stats match the
    file on disk
    """
    if p == STDIN_PATH or not cache:
        return False
    else:
        path = p.resolve()
        if path in cache:
            return _get_cache_info(path) == cache[path]
        else:
            return False


def write_cache(cache: Cache, results: List[SqlFormatResult], mode: Mode) -> None:
    """
    Updates cache with results, then dumps cache to disk
    """
    cache_file = get_cache_file()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    new_cache = cache.copy()
    for path in _gen_cache_keys_for_updates(results, mode):
        updated_info = _get_cache_info(path)
        new_cache[path] = updated_info
    with open(cache_file, "wb") as f:
        pickle.dump(new_cache, f)


def clear_cache() -> None:
    """
    Deletes the cache file on disk, if it exists
    """
    p = get_cache_file()
    try:
        p.unlink()
    except FileNotFoundError:
        pass


def _get_cache_info(path: Path) -> Tuple[float, int]:
    """
    Returns a tuple of (modified_time, file_size) for the path; this tuple is
    persisted to the cache, and we check the files on disk against this cached
    value to determine if we need to format the file again
    """
    stat = path.resolve().stat()
    file_info = (stat.st_mtime, stat.st_size)
    return file_info


def _gen_cache_keys_for_updates(
    results: Iterable[SqlFormatResult], mode: Mode
) -> Iterable[Path]:
    """
    Takes an interable of SqlfmtResults and yields paths to files that should
    be updated in the cache, based on the result of the sqlfmt run
    """
    gen = (
        res.source_path.resolve()
        for res in results
        if res.source_path
        and res.source_path != STDIN_PATH
        and _should_update_cache(res, mode)
    )
    yield from gen


def _should_update_cache(result: SqlFormatResult, mode: Mode) -> bool:
    """
    Takes a single SqlfmtResult and returns True if that result indicates that
    the associated file should be updated in the cache
    """
    if result.has_error or result.from_cache:
        return False
    elif not result.has_changed:
        return True
    elif mode.check or mode.diff:
        return False
    else:
        return True
