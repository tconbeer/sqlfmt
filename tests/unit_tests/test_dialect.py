from collections import Counter
from typing import Any

import pytest
from sqlfmt.dialect import ClickHouse, Dialect, Polyglot
from sqlfmt.rules.common import group


def test_group() -> None:
    regex = group(r"a", r"b", r"\d")
    assert regex == r"(a|b|\d)"

    group_of_one = group(r"\w+")
    assert group_of_one == r"(\w+)"


def test_dialect() -> None:
    # can't instantiate abc
    with pytest.raises(TypeError):
        _ = Dialect()  # type: ignore


class TestAllDialects:
    @pytest.fixture(params=[Polyglot, ClickHouse])
    def dialect(self, request: Any) -> Polyglot:
        d = request.param()
        assert isinstance(d, Polyglot)
        return d

    def test_rule_props_are_unique(self, dialect: Polyglot) -> None:
        ruleset = dialect.get_rules()
        name_counts = Counter([rule.name for rule in ruleset])
        assert max(name_counts.values()) == 1
        priority_counts = Counter([rule.priority for rule in ruleset])
        assert max(priority_counts.values()) == 1
        pattern_counts = Counter([rule.pattern for rule in ruleset])
        assert max(pattern_counts.values()) == 1


class TestPolyglot:
    @pytest.fixture
    def polyglot(self) -> Polyglot:
        return Polyglot()

    def test_case_insensitive(self, polyglot: Polyglot) -> None:
        assert polyglot.case_sensitive_names is False


class TestClickHouse:
    @pytest.fixture
    def clickhouse(self) -> ClickHouse:
        return ClickHouse()

    def test_case_sensitive(self, clickhouse: ClickHouse) -> None:
        assert clickhouse.case_sensitive_names is True
