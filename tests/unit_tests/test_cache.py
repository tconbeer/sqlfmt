import pickle
from pathlib import Path
from typing import Dict, Generator, List, Tuple

import pytest

from sqlfmt.cache import (
    Cache,
    check_cache,
    clear_cache,
    get_cache_file,
    load_cache,
    write_cache,
)
from sqlfmt.exception import SqlfmtError
from sqlfmt.mode import Mode
from sqlfmt.report import SqlFormatResult
from tests.util import BASE_DIR


@pytest.fixture(autouse=True)
def auto_clear_cache() -> Generator[None, None, None]:
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def sample_paths() -> Dict[str, Path]:
    paths = {
        "001": BASE_DIR / "preformatted" / "001_select_1.sql",
        "002": BASE_DIR / "preformatted" / "002_select_from_where.sql",
        "003": BASE_DIR / "preformatted" / "003_literals.sql",
        "004": BASE_DIR / "preformatted" / "004_with_select.sql",
        "005": BASE_DIR / "preformatted" / "005_fmt_off.sql",
        "900": BASE_DIR / "errors" / "900_bad_token.sql",
    }
    return paths


@pytest.fixture
def sample_stat() -> Tuple[float, int]:
    return (1000000000.100000, 1)


@pytest.fixture
def small_cache(sample_paths: Dict[str, Path], sample_stat: Tuple[float, int]) -> Cache:
    cache = {v: sample_stat for v in sample_paths.values() if "errors" not in str(v)}
    return cache


@pytest.fixture
def results_for_caching(sample_paths: Dict[str, Path]) -> List[SqlFormatResult]:
    results = [
        SqlFormatResult(
            sample_paths["001"],
            "select 1\n",
            "select 1\n",
            encoding="utf-8",
            utf_bom="",
        ),
        SqlFormatResult(
            sample_paths["002"],
            "select 1\n",
            "",
            encoding="utf-8",
            utf_bom="",
            from_cache=True,
        ),
        SqlFormatResult(
            sample_paths["003"],
            "select 'abc'\n",
            "select\n    'abc'\n",
            encoding="utf-8",
            utf_bom="",
        ),
        SqlFormatResult(
            sample_paths["900"],
            "!\n",
            "",
            encoding="utf-8",
            utf_bom="",
            exception=SqlfmtError("oops"),
        ),
    ]
    return results


def test_get_cache_file() -> None:
    cache_file = get_cache_file()
    assert cache_file
    assert isinstance(cache_file, Path)


def test_write_cache(
    small_cache: Cache,
    results_for_caching: List[SqlFormatResult],
    default_mode: Mode,
    sample_paths: Dict[str, Path],
    sample_stat: Tuple[float, int],
) -> None:
    cache_file = get_cache_file()
    assert not cache_file.exists()
    write_cache(cache=small_cache, results=results_for_caching, mode=default_mode)
    assert cache_file.exists()
    with open(cache_file, "rb") as f:
        written_cache = pickle.load(f)
    assert isinstance(written_cache, dict)
    assert small_cache.keys() == written_cache.keys()
    assert (
        written_cache[sample_paths["001"]] != sample_stat
    ), "Should write new stat to cache for unchanged files"
    assert (
        written_cache[sample_paths["002"]] == sample_stat
    ), "Should not write new stat to cache for results from cache"
    assert (
        written_cache[sample_paths["003"]] != sample_stat
    ), "Should write new stat to cache for changed files in default mode"
    assert sample_paths["900"] not in written_cache, "Should not write errors to cache"


def test_load_cache(
    small_cache: Cache,
    results_for_caching: List[SqlFormatResult],
    default_mode: Mode,
) -> None:
    empty_cache = load_cache()
    assert empty_cache == {}
    write_cache(cache=small_cache, results=results_for_caching, mode=default_mode)
    populated_cache = load_cache()
    assert isinstance(populated_cache, dict)
    assert populated_cache.keys() == small_cache.keys()
    assert populated_cache != small_cache


def test_check_cache(
    small_cache: Cache,
    results_for_caching: List[SqlFormatResult],
    default_mode: Mode,
    sample_paths: Dict[str, Path],
) -> None:
    assert all([not check_cache(small_cache, p) for p in sample_paths.values()])
    write_cache(cache=small_cache, results=results_for_caching, mode=default_mode)
    new_cache = load_cache()
    expected_cache_hits = [
        True,
        False,
        True,
        False,
        False,
        False,
    ]
    actual_cache_hits = [check_cache(new_cache, p) for p in sample_paths.values()]
    assert actual_cache_hits == expected_cache_hits


def test_clear_cache(
    small_cache: Cache,
    results_for_caching: List[SqlFormatResult],
    default_mode: Mode,
) -> None:
    cache_path = get_cache_file()
    write_cache(cache=small_cache, results=results_for_caching, mode=default_mode)
    assert cache_path.exists()

    clear_cache()
    assert not cache_path.exists()
