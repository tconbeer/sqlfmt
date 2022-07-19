from typing import Counter, Dict

import pytest

from sqlfmt.dialect import Dialect, Polyglot, Rule, group


def test_group() -> None:
    regex = group(r"a", r"b", r"\d")
    assert regex == r"(a|b|\d)"

    group_of_one = group(r"\w+")
    assert group_of_one == r"(\w+)"


def test_dialect() -> None:
    # can't instantiate abc
    with pytest.raises(TypeError):
        _ = Dialect()  # type: ignore


class TestPolyglot:
    @pytest.fixture(scope="class")
    def polyglot(self) -> Polyglot:
        return Polyglot()

    @pytest.fixture(scope="class")
    def rules_dict(self, polyglot: Polyglot) -> Dict[str, Dict[str, Rule]]:
        rules = polyglot.get_rules()
        d: Dict[str, Dict[str, Rule]] = {}
        for ruleset in rules:
            d[ruleset] = {rule.name: rule for rule in rules[ruleset]}
        return d

    def test_rule_props_are_unique(self, polyglot: Polyglot) -> None:
        rules = polyglot.get_rules()
        for ruleset in rules.keys():
            name_counts = Counter([rule.name for rule in rules[ruleset]])
            assert max(name_counts.values()) == 1
            priority_counts = Counter([rule.priority for rule in rules[ruleset]])
            assert max(priority_counts.values()) == 1
            pattern_counts = Counter([rule.pattern for rule in rules[ruleset]])
            assert max(pattern_counts.values()) == 1

    @pytest.mark.parametrize(
        "ruleset,rule_name,value",
        [
            ("main", "fmt_off", "-- fmt: off"),
            ("main", "fmt_off", "--FMT: off"),
            ("main", "fmt_off", "# fmt: off"),
            ("main", "fmt_on", "--fmt: ON"),
            ("main", "jinja_start", "{%"),
            ("main", "jinja_end", "}}"),
            ("main", "quoted_name", "`my_backticked_field_name`"),
            ("main", "quoted_name", "'my_quoted_literal'"),
            ("main", "quoted_name", '"my_quoted_field_name"'),
            ("main", "quoted_name", '"""triple " quotes!"""'),
            ("main", "quoted_name", "'''triple '' singles!\\'''"),
            ("main", "quoted_name", "$$ dollar delimited'$$"),
            ("main", "quoted_name", "$label$ dollar delimited with label$label$"),
            ("main", "quoted_name", "'single quote with '' doubled escape'"),
            ("main", "quoted_name", "'single quote \\' c escape'"),
            ("main", "quoted_name", '"double quote with "" doubled escape"'),
            ("main", "quoted_name", '"double quote \\" c escape"'),
            ("main", "quoted_name", "`backtick with \\` c escape`"),
            ("main", "quoted_name", 'r"bq raw string"'),
            ("main", "quoted_name", "U&'pg unicode string'"),
            ("main", "quoted_name", 'rb"""bq raw bytes string"""'),
            ("main", "quoted_name", '@"my!QUOTED!stage!name"'),
            ("main", "comment", "-- my comment"),
            ("main", "comment", "--no-space comment"),
            ("main", "comment", "# mysql-style # comments"),
            ("main", "comment", "#nospace"),
            ("main", "comment_start", "/*"),
            ("main", "comment_end", "*/"),
            ("main", "statement_start", "case"),
            ("main", "statement_end", "END"),
            ("main", "star", "*"),
            ("main", "number", "145.8"),
            ("main", "number", "-.58"),
            ("main", "bracket_open", "["),
            ("main", "bracket_close", ")"),
            ("main", "double_colon", "::"),
            ("main", "colon", ":"),
            ("main", "semicolon", ";"),
            ("main", "operator", "+"),
            ("main", "operator", "-"),
            ("main", "operator", "/"),
            ("main", "operator", "<>"),
            ("main", "operator", "||"),
            ("main", "operator", "=>"),
            ("main", "operator", "||/"),
            ("main", "operator", "|/"),
            ("main", "operator", "#"),
            ("main", "operator", ">>"),
            ("main", "operator", "<<"),
            ("main", "operator", "!"),
            ("main", "operator", "!="),
            # posix like/ not like
            ("main", "operator", "~"),
            ("main", "operator", "!~"),
            ("main", "operator", "~*"),
            ("main", "operator", "!~*"),
            # postgresql geo operators
            # see: https://www.postgresql.org/docs/current/functions-geometry.html
            ("main", "operator", "@-@"),
            ("main", "operator", "@@"),
            ("main", "operator", "##"),
            ("main", "operator", "<->"),
            ("main", "operator", "<@"),
            ("main", "operator", "@>"),
            ("main", "operator", "&&"),
            ("main", "operator", "&<"),
            ("main", "operator", "&>"),
            ("main", "operator", "<<|"),
            ("main", "operator", "|>>"),
            ("main", "operator", "&<|"),
            ("main", "operator", "|&>"),
            ("main", "operator", "<^"),
            ("main", "operator", ">^"),
            ("main", "operator", "?#"),
            ("main", "operator", "?-"),
            ("main", "operator", "?|"),
            ("main", "operator", "?-|"),
            ("main", "operator", "?||"),
            ("main", "operator", "~="),
            # network operators
            # see https://www.postgresql.org/docs/current/functions-net.html
            ("main", "operator", "<<="),
            ("main", "operator", ">>="),
            # json operators
            # see https://www.postgresql.org/docs/current/functions-json.html
            ("main", "operator", "->"),
            ("main", "operator", "->>"),
            ("main", "operator", "#>"),
            ("main", "operator", "#>>"),
            ("main", "operator", "-|-"),  # range adjacency
            ("main", "word_operator", "is"),
            ("main", "word_operator", "is not"),
            ("main", "word_operator", "in"),
            ("main", "word_operator", "not in"),
            ("main", "word_operator", "not\n\nin"),
            ("main", "word_operator", "like"),
            ("main", "word_operator", "not like"),
            ("main", "word_operator", "ilike"),
            ("main", "word_operator", "not ilike"),
            ("main", "word_operator", "like any"),
            ("main", "word_operator", "not like any"),
            ("main", "word_operator", "any"),
            ("main", "word_operator", "some"),
            ("main", "word_operator", "exists"),
            ("main", "word_operator", "not exists"),
            ("main", "word_operator", "all"),
            ("main", "word_operator", "grouping sets"),
            ("main", "word_operator", "cube"),
            ("main", "word_operator", "rollup"),
            ("main", "over", "over"),
            ("main", "as", "as"),
            ("main", "on", "on"),
            ("main", "boolean_operator", "AND"),
            ("main", "comma", ","),
            ("main", "dot", "."),
            ("main", "unterm_keyword", "select DISTINCT"),
            ("main", "unterm_keyword", "select"),
            ("main", "unterm_keyword", "select\n\t    distinct"),
            ("main", "unterm_keyword", "select top 25"),
            ("main", "unterm_keyword", "select all"),
            ("main", "unterm_keyword", "natural\t    full outer join"),
            ("main", "unterm_keyword", "left join"),
            ("main", "unterm_keyword", "cross join"),
            ("main", "unterm_keyword", "join"),
            ("main", "set_operator", "union"),
            ("main", "set_operator", "union all"),
            ("main", "set_operator", "intersect"),
            ("main", "set_operator", "minus"),
            ("main", "set_operator", "except"),
            ("main", "name", "my_table_45"),
            ("main", "name", "replace"),
            ("main", "other_identifiers", "$2"),
            ("main", "other_identifiers", "@my_unquoted_stage"),
            ("main", "newline", "\n"),
            ("jinja", "jinja_comment", "{# my comment #}"),
            ("jinja", "jinja_comment", "{#-my comment -#}"),
            ("jinja", "jinja_comment", "{#-\nmy\ncomment\n-#}"),
            ("jinja", "jinja_statement_start", "{%"),
            ("jinja", "jinja_statement_start", "{%-"),
            ("jinja", "jinja_expression_start", "{{"),
            ("jinja", "jinja_expression_start", "{{-"),
            ("jinja", "jinja_statement_end", "%}"),
            ("jinja", "jinja_statement_end", "-%}"),
            ("jinja", "jinja_expression_end", "}}"),
            ("jinja", "jinja_expression_end", "-}}"),
            ("jinja", "jinja_set_block_start", "{% set foo %}"),
            ("jinja", "jinja_set_block_start", "{% set my_long_variable %}"),
            ("jinja", "jinja_set_block_start", "{% set ns.my_namespace_var %}"),
            ("jinja", "jinja_set_block_end", "{% endset %}"),
            ("jinja", "jinja_set_block_end", "{%- endset %}"),
            ("jinja", "jinja_if_block_start", "{% if bar %}"),
            ("jinja", "jinja_if_block_start", "{%- if bar = baz -%}"),
            ("jinja", "jinja_if_block_start", "{%- if is_incremental() -%}"),
            ("jinja", "jinja_if_block_start", "{%- if loop.last -%}"),
            ("jinja", "jinja_elif_block_start", "{%- elif 1 > 2 -%}"),
            ("jinja", "jinja_else_block_start", "{% else %}"),
            ("jinja", "jinja_for_block_start", "{%- for foo in bar %}"),
            ("jinja", "jinja_macro_block_start", "{% macro my_macro(arg1, arg2) %}"),
            (
                "jinja",
                "jinja_test_block_start",
                "{% test my_test(model, column_name) %}",
            ),
            ("jinja", "jinja_snapshot_block_start", "{% snapshot snp_my_snapshot %}"),
            ("jinja", "jinja_if_block_end", "{% endif %}"),
            ("jinja", "jinja_if_block_end", "{%- endif -%}"),
            ("jinja", "jinja_for_block_end", "{% endfor %}"),
            ("jinja", "jinja_macro_block_end", "{% endmacro %}"),
            ("jinja", "jinja_test_block_end", "{% endtest %}"),
            ("jinja", "jinja_snapshot_block_end", "{% endsnapshot %}"),
        ],
    )
    def test_regex_exact_match(
        self,
        rules_dict: Dict[str, Dict[str, Rule]],
        ruleset: str,
        rule_name: str,
        value: str,
    ) -> None:
        rule = rules_dict[ruleset][rule_name]
        match = rule.program.match(value)
        assert match is not None, f"{rule_name} regex doesn't match {value}"
        start, end = match.span(1)

        assert (
            value[start:end] == value
        ), f"{rule_name} regex doesn't exactly match {value}"

    @pytest.mark.parametrize(
        "ruleset,rule_name,value",
        [
            ("main", "fmt_off", "# fmt:"),
            ("main", "fmt_off", "-- fmt: off but not really"),
            ("main", "jinja_start", "{"),
            ("main", "jinja_end", "}"),
            ("main", "quoted_name", "my_unquoted_name"),
            ("main", "double_colon", ":"),
            ("main", "operator", "."),
            ("main", "star_replace_exclude", "replace"),
            ("main", "unterm_keyword", "selection"),
            ("jinja", "jinja_set_block_start", "{% set foo = 'baz' %}"),
        ],
    )
    def test_regex_anti_match(
        self,
        rules_dict: Dict[str, Dict[str, Rule]],
        ruleset: str,
        rule_name: str,
        value: str,
    ) -> None:
        """make sure our compiled programs do not match these values"""
        rule = rules_dict[ruleset][rule_name]
        match = rule.program.match(value)
        assert match is None, f"{rule_name} regex should not match {value}"

    def test_regex_should_not_match_empty_string(self, polyglot: Polyglot) -> None:
        rules = polyglot.get_rules()
        for ruleset in rules.keys():
            for rule in rules[ruleset]:
                match = rule.program.match("")
                assert match is None, f"{ruleset}.{rule.name} rule matches empty string"
