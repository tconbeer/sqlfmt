from typing import List

import pytest

from sqlfmt.rule import JINJA, MAIN, Rule


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
        (MAIN, "statement_start", "case"),
        (MAIN, "statement_end", "END"),
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
        (MAIN, "comma", ","),
        (MAIN, "dot", "."),
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
        (MAIN, "word_operator", "using"),
        (MAIN, "unterm_keyword", "lateral flatten"),
        (MAIN, "unterm_keyword", "for"),
        (MAIN, "unterm_keyword", "select into"),
        (MAIN, "star_replace_exclude", "replace"),
        (MAIN, "unterm_keyword", "selection"),
        (MAIN, "unterm_keyword", "delete"),
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
    rules = [*MAIN, *JINJA]
    for rule in rules:
        match = rule.program.match("")
        assert match is None, f"{rule.name} rule matches empty string"
