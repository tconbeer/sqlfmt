import sys
from typing import Tuple

import pytest

from sqlfmt.jinjafmt import JinjaFormatter, JinjaTag
from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.node import Node
from sqlfmt.token import Token, TokenType


@pytest.fixture
def jinja_formatter(default_mode: Mode) -> JinjaFormatter:
    return JinjaFormatter(default_mode)


@pytest.fixture
def no_jinjafmt_mode() -> Mode:
    return Mode(no_jinjafmt=True)


@pytest.fixture
def disabled_jinja_formatter(no_jinjafmt_mode: Mode) -> JinjaFormatter:
    return JinjaFormatter(no_jinjafmt_mode)


@pytest.fixture
def uninstall_black(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "black", None)  # type: ignore


@pytest.mark.parametrize(
    "tag, result",
    [
        ("{{ expression }}", ("{{", "", "expression", "}}")),
        ("{{expression}}", ("{{", "", "expression", "}}")),
        ("{{- expression -}}", ("{{-", "", "expression", "-}}")),
        ("{{- expression }}", ("{{-", "", "expression", "}}")),
        ("{{ expression -}}", ("{{", "", "expression", "-}}")),
        ("{{expression-}}", ("{{", "", "expression", "-}}")),
        (
            "{{ my_macro(arg, kwarg=foo) }}",
            ("{{", "", "my_macro(arg, kwarg=foo)", "}}"),
        ),
        ("{% statement %}", ("{%", "", "statement", "%}")),
        ("{%- statement -%}", ("{%-", "", "statement", "-%}")),
        ("{% set a=1 %}", ("{%", "set ", "a=1", "%}")),
        ("{%set a=1%}", ("{%", "set ", "a=1", "%}")),
        ("{%-set a=1%}", ("{%-", "set ", "a=1", "%}")),
        ("{% SET a=1%}", ("{%", "set ", "a=1", "%}")),
        ("{% set my_var%}", ("{%", "set ", "my_var", "%}")),
        (
            "{% do my_list.append(something) %}",
            ("{%", "do ", "my_list.append(something)", "%}"),
        ),
    ],
)
def test_jinja_tag_from_string(tag: str, result: Tuple[str, str, str, str]) -> None:
    assert JinjaTag.from_string(tag, 0) == JinjaTag(*result, 0)


@pytest.mark.parametrize(
    "type,tag,formatted",
    [
        (TokenType.JINJA_EXPRESSION, "{{ expression }}", "{{ expression }}"),
        (TokenType.JINJA_EXPRESSION, "{{expression}}", "{{ expression }}"),
        (TokenType.JINJA_EXPRESSION, "{{- expression -}}", "{{- expression -}}"),
        (TokenType.JINJA_EXPRESSION, "{{- expression }}", "{{- expression }}"),
        (TokenType.JINJA_EXPRESSION, "{{ expression -}}", "{{ expression -}}"),
        (TokenType.JINJA_EXPRESSION, "{{expression-}}", "{{ expression -}}"),
        (
            TokenType.JINJA_EXPRESSION,
            "{{ my_macro(arg, kwarg=foo) }}",
            "{{ my_macro(arg, kwarg=foo) }}",
        ),
        (TokenType.JINJA_STATEMENT, "{% statement %}", "{% statement %}"),
        (TokenType.JINJA_STATEMENT, "{%- statement -%}", "{%- statement -%}"),
        (TokenType.JINJA_STATEMENT, "{% set a=1 %}", "{% set a = 1 %}"),
        (TokenType.JINJA_STATEMENT, "{%set a=1%}", "{% set a = 1 %}"),
        (TokenType.JINJA_STATEMENT, "{%-set a=1%}", "{%- set a = 1 %}"),
        (TokenType.JINJA_STATEMENT, "{% SET a=1%}", "{% set a = 1 %}"),
        (TokenType.JINJA_STATEMENT, "{% set my_var%}", "{% set my_var %}"),
        (
            TokenType.JINJA_STATEMENT,
            "{% do my_list.append( something ) %}",
            "{% do my_list.append(something) %}",
        ),
        # jinja allows line breaks where python doesn't; test try/except
        (
            TokenType.JINJA_STATEMENT,
            "{% set my_tuple = 1,\n    2,\n    3%}",
            "{% set my_tuple = 1, 2, 3 %}",
        ),
        # jinja allows "from" as an arg name, python doesn't
        (
            TokenType.JINJA_EXPRESSION,
            "{{dbt_utils.star(from=something)}}",
            "{{ dbt_utils.star(from=something) }}",
        ),
    ],
)
def test_format_jinja_node(
    jinja_formatter: JinjaFormatter, type: TokenType, tag: str, formatted: str
) -> None:
    t = Token(type=type, prefix="", token=tag, spos=0, epos=len(tag))
    n = Node.from_token(t, previous_node=None)
    jinja_formatter._format_jinja_node(n, 88)
    assert n.value == formatted


@pytest.mark.parametrize(
    "source_string",
    [
        "{% set a=1 %}",
        "{% set a    = 1 %}",
        '{{\n    dbt_utils.date_spine(\n        datepart="day",\n    )\n}}',
    ],
)
def test_no_format_jinja_node(
    disabled_jinja_formatter: JinjaFormatter, source_string: str
) -> None:
    t = Token(
        type=TokenType.JINJA_STATEMENT,
        prefix="",
        token=source_string,
        spos=0,
        epos=len(source_string),
    )
    n = Node.from_token(t, previous_node=None)
    disabled_jinja_formatter._format_jinja_node(n, 88)
    assert n.value == source_string


@pytest.mark.parametrize(
    "source_string",
    [
        "{% set a=1 %}",
        "{% set a    = 1 %}",
        '{{\n    dbt_utils.date_spine(\n        datepart="day",\n    )\n}}',
    ],
)
def test_format_jinja_node_no_black(
    uninstall_black: None, jinja_formatter: JinjaFormatter, source_string: str
) -> None:
    t = Token(
        type=TokenType.JINJA_STATEMENT,
        prefix="",
        token=source_string,
        spos=0,
        epos=len(source_string),
    )
    n = Node.from_token(t, previous_node=None)
    jinja_formatter._format_jinja_node(n, 88)
    assert n.value == source_string


def test_format_line(jinja_formatter: JinjaFormatter) -> None:
    t = Token(
        type=TokenType.JINJA_EXPRESSION,
        prefix="",
        token="{{expression}}",
        spos=0,
        epos=14,
    )
    n = Node.from_token(t, previous_node=None)
    line = Line.from_nodes(previous_node=None, nodes=[n], comments=[])
    line.append_newline()

    assert n.value == "{{expression}}"
    _ = list(map(jinja_formatter.format_line, [line]))
    assert n.value == "{{ expression }}"


def test_black_wrapper_format_string_no_black(
    uninstall_black: None, default_mode: Mode
) -> None:
    source_string = "1 +    1"
    jinja_formatter = JinjaFormatter(default_mode)
    result = jinja_formatter.code_formatter.format_string(
        source_string=source_string, max_length=88
    )
    assert result == source_string


@pytest.mark.parametrize(
    "tag,expected",
    [
        (JinjaTag("{{", "", "any code!", "}}", 0), 88 - 2 - 2 - 2),
        (JinjaTag("{%-", "set", "_", "%}", 0), 88 - 3 - 3 - 2 - 2),
    ],
)
def test_max_code_length(tag: JinjaTag, expected: int) -> None:
    result = tag.max_code_length(88)
    assert result == expected
