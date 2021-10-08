from pathlib import Path
from typing import List, Tuple

TEST_DIR = Path(__file__).parent
BASE_DIR = TEST_DIR / "data"


def read_test_data(relpath: str) -> Tuple[str, str]:
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

    return "".join(source_query).strip() + "\n", "".join(formatted_query).strip() + "\n"


def check_formatting(expected: str, actual: str) -> None:

    try:
        assert (
            expected == actual
        ), "Formatting error. Output file written to tests/.results/"
    except AssertionError as e:
        import inspect

        caller = inspect.stack()[1].function
        results_dir = p = TEST_DIR / ".results"
        results_dir.mkdir(exist_ok=True)
        p = results_dir / (caller + ".sql")
        with open(p, "w") as f:
            f.write(actual)
        raise e
