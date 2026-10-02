import pytest

from sqlfmt.api import format_string
from sqlfmt.mode import Mode


@pytest.mark.parametrize(
    "statement",
    [
        "create table t (id int);\n",
        "grant select on t to role reader;\n",
        "pragma threads=4;\n",
        "create table t clone source;\n",
        "create warehouse w;\n",
        "create function f() returns int as '1';\n",
        "create function f() returns int as (1);\n",
    ],
)
def test_format_many_ruleset_switches(statement: str, default_mode: Mode) -> None:
    source = statement * 1000 + "SELECT 1;\n"
    expected = format_string(statement, default_mode) * 1000 + "select 1\n;\n"

    assert format_string(source, default_mode) == expected
