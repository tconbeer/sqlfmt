from collections import Counter
from typing import List

import pytest

from sqlfmt.rule import CORE, CREATE_FUNCTION, GRANT, JINJA, MAIN, Rule


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
        (CORE, "fmt_off", "-- fmt: off"),
        (CORE, "fmt_off", "--FMT: off"),
        (CORE, "fmt_off", "# fmt: off"),
        (CORE, "fmt_on", "--fmt: ON"),
        (CORE, "jinja_start", "{%"),
        (CORE, "jinja_end", "}}"),
        (CORE, "quoted_name", "`my_backticked_field_name`"),
        (CORE, "quoted_name", "'my_quoted_literal'"),
        (CORE, "quoted_name", '"my_quoted_field_name"'),
        (CORE, "quoted_name", '"""triple " quotes!"""'),
        (CORE, "quoted_name", "'''triple '' singles!\\'''"),
        (CORE, "quoted_name", "$$ dollar \ndelimited'$$"),
        (CORE, "quoted_name", "$$ SELECT $1, CAST($1 AS text) || ' is text' $$"),
        (CORE, "quoted_name", "$label$ dollar delimited with label$label$"),
        (CORE, "quoted_name", "'single quote with '' doubled escape'"),
        (CORE, "quoted_name", "'single quote \\' c escape'"),
        (CORE, "quoted_name", '"double quote with "" doubled escape"'),
        (CORE, "quoted_name", '"double quote \\" c escape"'),
        (CORE, "quoted_name", "`backtick with \\` c escape`"),
        (CORE, "quoted_name", 'r"bq raw string"'),
        (CORE, "quoted_name", "U&'pg unicode string'"),
        (CORE, "quoted_name", 'rb"""bq raw bytes string"""'),
        (CORE, "quoted_name", '@"my!QUOTED!stage!name"'),
        (CORE, "comment", "-- my comment"),
        (CORE, "comment", "--no-space comment"),
        (CORE, "comment", "# mysql-style # comments"),
        (CORE, "comment", "#nospace"),
        (CORE, "comment_start", "/*"),
        (CORE, "comment_end", "*/"),
        (MAIN, "statement_start", "case"),
        (MAIN, "statement_end", "END"),
        (CORE, "star", "*"),
        (CORE, "number", "145.8"),
        (CORE, "number", "-.58"),
        (CORE, "bracket_open", "["),
        (CORE, "bracket_close", ")"),
        (CORE, "double_colon", "::"),
        (CORE, "colon", ":"),
        (CORE, "semicolon", ";"),
        (CORE, "operator", "+"),
        (CORE, "operator", "-"),
        (CORE, "operator", "/"),
        (CORE, "operator", "%"),
        (CORE, "operator", "%%"),
        (CORE, "operator", ">="),
        (CORE, "operator", "<>"),
        (CORE, "operator", "||"),
        (CORE, "operator", "=>"),
        (CORE, "operator", "||/"),
        (CORE, "operator", "|/"),
        (CORE, "operator", "#"),
        (CORE, "operator", ">>"),
        (CORE, "operator", "<<"),
        (CORE, "operator", "!"),
        (CORE, "operator", "!="),
        # posix like/ not like
        (CORE, "operator", "~"),
        (CORE, "operator", "!~"),
        (CORE, "operator", "~*"),
        (CORE, "operator", "!~*"),
        # postgresql geo operators
        # see: https://www.postgresql.org/docs/current/functions-geometry.html
        (CORE, "operator", "@-@"),
        (CORE, "operator", "@@"),
        (CORE, "operator", "##"),
        (CORE, "operator", "<->"),
        (CORE, "operator", "<@"),
        (CORE, "operator", "@>"),
        (CORE, "operator", "&&"),
        (CORE, "operator", "&<"),
        (CORE, "operator", "&>"),
        (CORE, "operator", "<<|"),
        (CORE, "operator", "|>>"),
        (CORE, "operator", "&<|"),
        (CORE, "operator", "|&>"),
        (CORE, "operator", "<^"),
        (CORE, "operator", ">^"),
        (CORE, "operator", "?#"),
        (CORE, "operator", "?-"),
        (CORE, "operator", "?|"),
        (CORE, "operator", "?-|"),
        (CORE, "operator", "?||"),
        (CORE, "operator", "~="),
        # network operators
        # see https://www.postgresql.org/docs/current/functions-net.html
        (CORE, "operator", "<<="),
        (CORE, "operator", ">>="),
        # json operators
        # see https://www.postgresql.org/docs/current/functions-json.html
        (CORE, "operator", "->"),
        (CORE, "operator", "->>"),
        (CORE, "operator", "#>"),
        (CORE, "operator", "#>>"),
        (CORE, "operator", "-|-"),  # range adjacency
        (MAIN, "word_operator", "is"),
        (MAIN, "word_operator", "is not"),
        (MAIN, "word_operator", "in"),
        (MAIN, "word_operator", "not in"),
        (MAIN, "word_operator", "not\n\nin"),
        (MAIN, "word_operator", "like"),
        (MAIN, "word_operator", "not like"),
        (MAIN, "word_operator", "ilike"),
        (MAIN, "word_operator", "not ilike"),
        (MAIN, "word_operator", "like any"),
        (MAIN, "word_operator", "not like any"),
        (MAIN, "word_operator", "any"),
        (MAIN, "word_operator", "some"),
        (MAIN, "word_operator", "exists"),
        (MAIN, "word_operator", "not exists"),
        (MAIN, "word_operator", "all"),
        (MAIN, "word_operator", "grouping sets"),
        (MAIN, "word_operator", "cube"),
        (MAIN, "word_operator", "rollup"),
        (MAIN, "word_operator", "over"),
        (MAIN, "word_operator", "within group"),
        (MAIN, "word_operator", "filter"),
        (MAIN, "word_operator", "as"),
        (MAIN, "word_operator", "tablesample"),
        (MAIN, "word_operator", "pivot"),
        (MAIN, "word_operator", "unpivot"),
        (MAIN, "on", "on"),
        (MAIN, "boolean_operator", "AND"),
        (CORE, "comma", ","),
        (CORE, "dot", "."),
        (MAIN, "unterm_keyword", "select DISTINCT"),
        (MAIN, "unterm_keyword", "select"),
        (MAIN, "unterm_keyword", "select\n\t    distinct"),
        (MAIN, "unterm_keyword", "select top 25"),
        (MAIN, "unterm_keyword", "select all"),
        (MAIN, "unterm_keyword", "natural\t    full outer join"),
        (MAIN, "unterm_keyword", "left join"),
        (MAIN, "unterm_keyword", "cross join"),
        (MAIN, "unterm_keyword", "join"),
        (MAIN, "unterm_keyword", "values"),
        (MAIN, "unterm_keyword", "cluster by"),
        (MAIN, "unterm_keyword", "sort\nby"),
        (MAIN, "unterm_keyword", "distribute\t by"),
        (MAIN, "unterm_keyword", "lateral view"),
        (MAIN, "unterm_keyword", "lateral view outer"),
        (MAIN, "unterm_keyword", "delete from"),
        (MAIN, "set_operator", "union"),
        (MAIN, "set_operator", "union all"),
        (MAIN, "set_operator", "intersect"),
        (MAIN, "set_operator", "minus"),
        (MAIN, "set_operator", "except"),
        (CORE, "bracket_open", "array<"),
        (CORE, "bracket_open", "table\n<"),
        (CORE, "bracket_open", "struct<"),
        (MAIN, "explain", "explain"),
        (MAIN, "explain", "explain analyze"),
        (MAIN, "explain", "explain using text"),
        (MAIN, "grant", "grant"),
        (MAIN, "grant", "revoke"),
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
                "create table my_table as\n"
                "--table comment; another comment;\n"
                "(select * from foo)"
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
        (GRANT, "unterm_keyword", "grant"),
        (GRANT, "unterm_keyword", "revoke"),
        (GRANT, "unterm_keyword", "revoke grant option for"),
        (GRANT, "unterm_keyword", "to"),
        (GRANT, "unterm_keyword", "from"),
        (GRANT, "unterm_keyword", "with grant option"),
        (CREATE_FUNCTION, "unterm_keyword", "create temp function"),
        (CREATE_FUNCTION, "unterm_keyword", "CREATE OR REPLACE TABLE FUNCTION"),
        (CREATE_FUNCTION, "unterm_keyword", "language"),
        (CREATE_FUNCTION, "unterm_keyword", "called on null input"),
        (CREATE_FUNCTION, "unterm_keyword", "returns\nnull on null input"),
        (CREATE_FUNCTION, "unterm_keyword", "not null"),
        (CREATE_FUNCTION, "unterm_keyword", "handler"),
        (CREATE_FUNCTION, "unterm_keyword", "packages"),
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
        (CORE, "fmt_off", "# fmt:"),
        (CORE, "fmt_off", "-- fmt: off but not really"),
        (CORE, "jinja_start", "{"),
        (CORE, "jinja_end", "}"),
        (CORE, "quoted_name", "my_unquoted_name"),
        (CORE, "double_colon", ":"),
        (CORE, "operator", "."),
        (CORE, "operator", ">"),
        (MAIN, "word_operator", "using"),
        (MAIN, "unterm_keyword", "lateral flatten"),
        (MAIN, "unterm_keyword", "for"),
        (MAIN, "unterm_keyword", "MAIN into"),
        (MAIN, "star_replace_exclude", "replace"),
        (MAIN, "unterm_keyword", "MAINion"),
        (MAIN, "unterm_keyword", "delete"),
        (MAIN, "unsupported_ddl", "insert('abc', 1, 2, 'Z')"),
        (JINJA, "jinja_set_block_start", "{% set foo = 'baz' %}"),
        (GRANT, "unterm_keyword", "select"),
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
    rules = [*CORE, *MAIN, *JINJA, *GRANT]
    for rule in rules:
        match = rule.program.match("")
        assert match is None, f"{rule.name} rule matches empty string"


def test_core_priority_range() -> None:
    for rule in CORE:
        assert rule.priority >= 0
        assert rule.priority < 10000
        #  this range reserved for other rulesets
        assert not (rule.priority > 1000 and rule.priority < 5000)


@pytest.mark.parametrize("ruleset", [CORE, MAIN, JINJA, GRANT])
def test_rule_priorities_unique_within_ruleset(ruleset: List[Rule]) -> None:
    name_counts = Counter([rule.name for rule in ruleset])
    assert max(name_counts.values()) == 1
    priority_counts = Counter([rule.priority for rule in ruleset])
    assert max(priority_counts.values()) == 1
    pattern_counts = Counter([rule.pattern for rule in ruleset])
    assert max(pattern_counts.values()) == 1
