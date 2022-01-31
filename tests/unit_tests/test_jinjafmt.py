from typing import Tuple

import pytest

from sqlfmt.jinjafmt import JinjaFormatter
from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode
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
        ("{% set a=1 %}", ("{%", "set", "a=1", "%}")),
        ("{%set a=1%}", ("{%", "set", "a=1", "%}")),
        ("{%-set a=1%}", ("{%-", "set", "a=1", "%}")),
        ("{% SET a=1%}", ("{%", "SET", "a=1", "%}")),
        ("{% set my_var%}", ("{%", "set", "my_var", "%}")),
        (
            "{% do my_list.append(something) %}",
            ("{%", "do", "my_list.append(something)", "%}"),
        ),
    ],
)
def test_split_jinja_tag_contents(
    jinja_formatter: JinjaFormatter, tag: str, result: Tuple[str, str, str, str]
) -> None:
    assert jinja_formatter._split_jinja_tag_contents(tag) == result


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
    ],
)
def test_format_jinja_node(
    jinja_formatter: JinjaFormatter, type: TokenType, tag: str, formatted: str
) -> None:
    t = Token(type=type, prefix="", token=tag, spos=0, epos=len(tag))
    n = Node.from_token(t, previous_node=None)
    jinja_formatter.format_jinja_node(n, 88)
    assert n.value == formatted


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
