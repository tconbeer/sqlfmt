from collections import Counter
from typing import List

import pytest

from sqlfmt.rule import JINJA, MAIN, SELECT, Rule


def get_rule(ruleset: List[Rule], rule_name: str) -> Rule:
    """
    Return the rule from ruleset that matches rule_name
    """
    matching_rules = filter(lambda rule: rule.name == rule_name, ruleset)
    try:
        return next(matching_rules)
    except StopIteration:
        raise ValueError(f"No rule '{rule_name}' in ruleset '{ruleset}'")


@pytest.mark.parametrize(
    "ruleset,rule_name,value",
    [
        (MAIN, "fmt_off", "-- fmt: off"),
        (MAIN, "fmt_off", "--FMT: off"),
        (MAIN, "fmt_off", "# fmt: off"),
        (MAIN, "fmt_on", "--fmt: ON"),
        (MAIN, "jinja_start", "{%"),
        (MAIN, "jinja_end", "}}"),
        (MAIN, "quoted_name", "`my_backticked_field_name`"),
        (MAIN, "quoted_name", "'my_quoted_literal'"),
        (MAIN, "quoted_name", '"my_quoted_field_name"'),
        (MAIN, "quoted_name", '"""triple " quotes!"""'),
        (MAIN, "quoted_name", "'''triple '' singles!\\'''"),
        (MAIN, "quoted_name", "$$ dollar delimited'$$"),
        (MAIN, "quoted_name", "$label$ dollar delimited with label$label$"),
        (MAIN, "quoted_name", "'single quote with '' doubled escape'"),
        (MAIN, "quoted_name", "'single quote \\' c escape'"),
        (MAIN, "quoted_name", '"double quote with "" doubled escape"'),
        (MAIN, "quoted_name", '"double quote \\" c escape"'),
        (MAIN, "quoted_name", "`backtick with \\` c escape`"),
        (MAIN, "quoted_name", 'r"bq raw string"'),
        (MAIN, "quoted_name", "U&'pg unicode string'"),
        (MAIN, "quoted_name", 'rb"""bq raw bytes string"""'),
        (MAIN, "quoted_name", '@"my!QUOTED!stage!name"'),
        (MAIN, "comment", "-- my comment"),
        (MAIN, "comment", "--no-space comment"),
        (MAIN, "comment", "# mysql-style # comments"),
        (MAIN, "comment", "#nospace"),
        (MAIN, "comment_start", "/*"),
        (MAIN, "comment_end", "*/"),
        (SELECT, "statement_start", "case"),
        (SELECT, "statement_end", "END"),
        (MAIN, "star", "*"),
        (MAIN, "number", "145.8"),
        (MAIN, "number", "-.58"),
        (MAIN, "bracket_open", "["),
        (MAIN, "bracket_close", ")"),
        (MAIN, "double_colon", "::"),
        (MAIN, "colon", ":"),
        (MAIN, "semicolon", ";"),
        (MAIN, "operator", "+"),
        (MAIN, "operator", "-"),
        (MAIN, "operator", "/"),
        (MAIN, "operator", "%"),
        (MAIN, "operator", "%%"),
        (MAIN, "operator", "<>"),
        (MAIN, "operator", "||"),
        (MAIN, "operator", "=>"),
        (MAIN, "operator", "||/"),
        (MAIN, "operator", "|/"),
        (MAIN, "operator", "#"),
        (MAIN, "operator", ">>"),
        (MAIN, "operator", "<<"),
        (MAIN, "operator", "!"),
        (MAIN, "operator", "!="),
        # posix like/ not like
        (MAIN, "operator", "~"),
        (MAIN, "operator", "!~"),
        (MAIN, "operator", "~*"),
        (MAIN, "operator", "!~*"),
        # postgresql geo operators
        # see: https://www.postgresql.org/docs/current/functions-geometry.html
        (MAIN, "operator", "@-@"),
        (MAIN, "operator", "@@"),
        (MAIN, "operator", "##"),
        (MAIN, "operator", "<->"),
        (MAIN, "operator", "<@"),
        (MAIN, "operator", "@>"),
        (MAIN, "operator", "&&"),
        (MAIN, "operator", "&<"),
        (MAIN, "operator", "&>"),
        (MAIN, "operator", "<<|"),
        (MAIN, "operator", "|>>"),
        (MAIN, "operator", "&<|"),
        (MAIN, "operator", "|&>"),
        (MAIN, "operator", "<^"),
        (MAIN, "operator", ">^"),
        (MAIN, "operator", "?#"),
        (MAIN, "operator", "?-"),
        (MAIN, "operator", "?|"),
        (MAIN, "operator", "?-|"),
        (MAIN, "operator", "?||"),
        (MAIN, "operator", "~="),
        # network operators
        # see https://www.postgresql.org/docs/current/functions-net.html
        (MAIN, "operator", "<<="),
        (MAIN, "operator", ">>="),
        # json operators
        # see https://www.postgresql.org/docs/current/functions-json.html
        (MAIN, "operator", "->"),
        (MAIN, "operator", "->>"),
        (MAIN, "operator", "#>"),
        (MAIN, "operator", "#>>"),
        (MAIN, "operator", "-|-"),  # range adjacency
        (SELECT, "word_operator", "is"),
        (SELECT, "word_operator", "is not"),
        (SELECT, "word_operator", "in"),
        (SELECT, "word_operator", "not in"),
        (SELECT, "word_operator", "not\n\nin"),
        (SELECT, "word_operator", "like"),
        (SELECT, "word_operator", "not like"),
        (SELECT, "word_operator", "ilike"),
        (SELECT, "word_operator", "not ilike"),
        (SELECT, "word_operator", "like any"),
        (SELECT, "word_operator", "not like any"),
        (SELECT, "word_operator", "any"),
        (SELECT, "word_operator", "some"),
        (SELECT, "word_operator", "exists"),
        (SELECT, "word_operator", "not exists"),
        (SELECT, "word_operator", "all"),
        (SELECT, "word_operator", "grouping sets"),
        (SELECT, "word_operator", "cube"),
        (SELECT, "word_operator", "rollup"),
        (SELECT, "word_operator", "over"),
        (SELECT, "word_operator", "within group"),
        (SELECT, "word_operator", "filter"),
        (SELECT, "word_operator", "as"),
        (SELECT, "word_operator", "tablesample"),
        (SELECT, "word_operator", "pivot"),
        (SELECT, "word_operator", "unpivot"),
        (SELECT, "on", "on"),
        (SELECT, "boolean_operator", "AND"),
        (MAIN, "comma", ","),
        (MAIN, "dot", "."),
        (SELECT, "unterm_keyword", "select DISTINCT"),
        (SELECT, "unterm_keyword", "select"),
        (SELECT, "unterm_keyword", "select\n\t    distinct"),
        (SELECT, "unterm_keyword", "select top 25"),
        (SELECT, "unterm_keyword", "select all"),
        (SELECT, "unterm_keyword", "natural\t    full outer join"),
        (SELECT, "unterm_keyword", "left join"),
        (SELECT, "unterm_keyword", "cross join"),
        (SELECT, "unterm_keyword", "join"),
        (SELECT, "unterm_keyword", "values"),
        (SELECT, "unterm_keyword", "cluster by"),
        (SELECT, "unterm_keyword", "sort\nby"),
        (SELECT, "unterm_keyword", "distribute\t by"),
        (SELECT, "unterm_keyword", "lateral view"),
        (SELECT, "unterm_keyword", "lateral view outer"),
        (SELECT, "unterm_keyword", "delete from"),
        (SELECT, "set_operator", "union"),
        (SELECT, "set_operator", "union all"),
        (SELECT, "set_operator", "intersect"),
        (SELECT, "set_operator", "minus"),
        (SELECT, "set_operator", "except"),
        (MAIN, "bq_typed_array", "array<INT64>"),
        (MAIN, "nonreserved_keyword", "explain"),
        (MAIN, "nonreserved_keyword", "explain analyze"),
        (MAIN, "nonreserved_keyword", "explain using text"),
        (MAIN, "unsupported_ddl", "create table"),
        (MAIN, "unsupported_ddl", "select\ninto"),
        (MAIN, "unsupported_ddl", "insert"),
        (MAIN, "unsupported_ddl", "insert into"),
        (MAIN, "unsupported_ddl", "insert overwrite"),
        (MAIN, "unsupported_ddl", "insert overwrite into"),
        (MAIN, "unsupported_ddl", "update"),
        (
            MAIN,
            "unsupported_ddl",
            (
                "create function foo()\n"
                "--fn comment; another comment;\n"
                "returns int language javascript as $$foo;$$"
            ),
        ),
        (MAIN, "name", "my_table_45"),
        (MAIN, "name", "replace"),
        (MAIN, "other_identifiers", "$2"),
        (MAIN, "other_identifiers", "@my_unquoted_stage"),
        (MAIN, "other_identifiers", "%s"),
        (MAIN, "other_identifiers", "%(name)s"),
        (MAIN, "other_identifiers", "%(anything! else!)s"),
        (MAIN, "newline", "\n"),
        (JINJA, "jinja_comment", "{# my comment #}"),
        (JINJA, "jinja_comment", "{#-my comment -#}"),
        (JINJA, "jinja_comment", "{#-\nmy\ncomment\n-#}"),
        (JINJA, "jinja_statement_start", "{%"),
        (JINJA, "jinja_statement_start", "{%-"),
        (JINJA, "jinja_expression_start", "{{"),
        (JINJA, "jinja_expression_start", "{{-"),
        (JINJA, "jinja_statement_end", "%}"),
        (JINJA, "jinja_statement_end", "-%}"),
        (JINJA, "jinja_expression_end", "}}"),
        (JINJA, "jinja_expression_end", "-}}"),
        (JINJA, "jinja_set_block_start", "{% set foo %}"),
        (JINJA, "jinja_set_block_start", "{% set my_long_variable %}"),
        (JINJA, "jinja_set_block_start", "{% set ns.my_namespace_var %}"),
        (JINJA, "jinja_set_block_end", "{% endset %}"),
        (JINJA, "jinja_set_block_end", "{%- endset %}"),
        (JINJA, "jinja_if_block_start", "{% if bar %}"),
        (JINJA, "jinja_if_block_start", "{%- if bar = baz -%}"),
        (JINJA, "jinja_if_block_start", "{%- if is_incremental() -%}"),
        (JINJA, "jinja_if_block_start", "{%- if loop.last -%}"),
        (JINJA, "jinja_elif_block_start", "{%- elif 1 > 2 -%}"),
        (JINJA, "jinja_else_block_start", "{% else %}"),
        (JINJA, "jinja_for_block_start", "{%- for foo in bar %}"),
        (JINJA, "jinja_macro_block_start", "{% macro my_macro(arg1, arg2) %}"),
        (
            JINJA,
            "jinja_test_block_start",
            "{% test my_test(model, column_name) %}",
        ),
        (JINJA, "jinja_snapshot_block_start", "{% snapshot snp_my_snapshot %}"),
        (JINJA, "jinja_if_block_end", "{% endif %}"),
        (JINJA, "jinja_if_block_end", "{%- endif -%}"),
        (JINJA, "jinja_for_block_end", "{% endfor %}"),
        (JINJA, "jinja_macro_block_end", "{% endmacro %}"),
        (JINJA, "jinja_test_block_end", "{% endtest %}"),
        (JINJA, "jinja_snapshot_block_end", "{% endsnapshot %}"),
    ],
)
def test_regex_exact_match(
    ruleset: List[Rule],
    rule_name: str,
    value: str,
) -> None:
    rule = get_rule(ruleset, rule_name)
    match = rule.program.match(value)
    assert match is not None, f"{rule_name} regex doesn't match {value}"
    start, end = match.span(1)

    assert value[start:end] == value, f"{rule_name} regex doesn't exactly match {value}"


@pytest.mark.parametrize(
    "ruleset,rule_name,value",
    [
        (MAIN, "fmt_off", "# fmt:"),
        (MAIN, "fmt_off", "-- fmt: off but not really"),
        (MAIN, "jinja_start", "{"),
        (MAIN, "jinja_end", "}"),
        (MAIN, "quoted_name", "my_unquoted_name"),
        (MAIN, "double_colon", ":"),
        (MAIN, "operator", "."),
        (SELECT, "word_operator", "using"),
        (SELECT, "unterm_keyword", "lateral flatten"),
        (SELECT, "unterm_keyword", "for"),
        (SELECT, "unterm_keyword", "select into"),
        (SELECT, "star_replace_exclude", "replace"),
        (SELECT, "unterm_keyword", "selection"),
        (SELECT, "unterm_keyword", "delete"),
        (MAIN, "unsupported_ddl", "insert('abc', 1, 2, 'Z')"),
        (
            MAIN,
            "bq_typed_array",
            "array < something and int64 > something_else[0]",
        ),
        (JINJA, "jinja_set_block_start", "{% set foo = 'baz' %}"),
    ],
)
def test_regex_anti_match(
    ruleset: List[Rule],
    rule_name: str,
    value: str,
) -> None:
    """make sure our compiled programs do not match these values"""
    rule = get_rule(ruleset, rule_name)
    match = rule.program.match(value)
    assert match is None, f"{rule_name} regex should not match {value}"


def test_regex_should_not_match_empty_string() -> None:
    rules = [*MAIN, *SELECT, *JINJA]
    for rule in rules:
        match = rule.program.match("")
        assert match is None, f"{rule.name} rule matches empty string"


def test_main_priority_range() -> None:
    for rule in MAIN:
        assert rule.priority >= 0
        assert rule.priority < 10000
        #  this range reserved for other rulesets
        assert not (rule.priority > 1000 and rule.priority < 3000)


def test_select_priority_range() -> None:
    for rule in SELECT:
        assert rule.priority >= 1000
        assert rule.priority < 3000


@pytest.mark.parametrize("ruleset", [MAIN, SELECT, JINJA])
def test_rule_priorities_unique_within_ruleset(ruleset: List[Rule]) -> None:
    name_counts = Counter([rule.name for rule in ruleset])
    assert max(name_counts.values()) == 1
    priority_counts = Counter([rule.priority for rule in ruleset])
    assert max(priority_counts.values()) == 1
    pattern_counts = Counter([rule.pattern for rule in ruleset])
    assert max(pattern_counts.values()) == 1
