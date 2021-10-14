from pathlib import Path

from sqlfmt.mode import Mode
from sqlfmt.utils import gen_sql_files


def test_file_discovery() -> None:
    p = Path("tests/data/unit_tests/test_utils/test_file_discovery")
    res = list(gen_sql_files(p.iterdir(), Mode()))

    expected = (
        p / "top_level_file.sql",
        p / "a_directory/one_file.sql",
        p / "a_directory/nested_directory/another_file.sql",
        p / "a_directory/nested_directory/j2_extension.sql.jinja",
    )

    for p in expected:
        assert p in res
