import shutil
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple, Union

TEST_DIR = Path(__file__).parent
BASE_DIR = TEST_DIR / "data"
RESULTS_DIR = TEST_DIR / ".results"


def read_test_data(relpath: Union[Path, str]) -> Tuple[str, str]:
    """reads a test file contents and returns a tuple of strings corresponding to
    the unformatted and formatted examples in the test file. If the test file doesn't
    include a ')))))__SQLFMT_OUTPUT__(((((' sentinel, returns the same string twice
    (as the input is assumed to be pre-formatted). relpath is relative to
    tests/data/"""
    SENTINEL = ")))))__SQLFMT_OUTPUT__((((("

    test_path = BASE_DIR / relpath

    with open(test_path, "r") as test_file:
        lines = test_file.readlines()

    source_query: List[str] = []
    formatted_query: List[str] = []

    target = source_query

    for line in lines:
        if line.rstrip() == SENTINEL:
            target = formatted_query
            continue
        target.append(line)

    if source_query and not formatted_query:
        formatted_query = source_query[:]

    return "".join(source_query).strip() + "\n", "".join(formatted_query)


def _safe_create_results_dir() -> Path:
    results_dir = RESULTS_DIR
    results_dir.mkdir(exist_ok=True)
    return results_dir


def delete_results_dir() -> None:
    shutil.rmtree(RESULTS_DIR, ignore_errors=True)


def check_formatting(expected: str, actual: str, ctx: str = "") -> None:
    try:
        assert (
            expected == actual
        ), "Formatting error. Output file written to tests/.results/"
    except AssertionError as e:
        import inspect

        results_dir = _safe_create_results_dir()

        caller = inspect.stack()[1].function
        if ctx:
            caller += "-"
            ctx = ctx.replace("/", "-")

        if ctx.endswith(".sql"):
            suffix = ""
        else:
            suffix = ".sql"

        p = results_dir / (caller + ctx + suffix)
        with open(p, "w") as f:
            f.write(actual)
        raise e


def discover_test_files(relpaths: Iterable[Union[str, Path]]) -> Iterator[Path]:
    for p in [BASE_DIR / p for p in relpaths]:
        if p.is_file() and p.suffix in [".sql", ".md"]:
            yield p
        elif p.is_dir():
            yield from (discover_test_files(p.iterdir()))


def copy_test_data_to_tmp(relpaths: List[str], tmp_path: Path) -> Path:
    """
    Reads in test data from an existing file or directory, and creates a new file
    at the temp_path with the source query from the original test data file.

    Returns the path to the temporary file
    """

    for abspath in discover_test_files(relpaths):
        file_contents, _ = read_test_data(abspath)

        with open(tmp_path / abspath.name, "w") as tmp_file:
            tmp_file.write(file_contents)

    return tmp_path


def copy_config_file_to_dst(file_name: str, dst_path: Path) -> Path:
    CONFIG_DIR = BASE_DIR / "config"
    file_path = CONFIG_DIR / file_name
    assert file_path.is_file()

    new_file_path = dst_path / "pyproject.toml"
    shutil.copyfile(file_path, new_file_path)
    return new_file_path
