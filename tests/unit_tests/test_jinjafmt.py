import sys
from typing import Dict, Tuple

import pytest
from sqlfmt.analyzer import Analyzer
from sqlfmt.jinjafmt import BlackWrapper, JinjaFormatter, JinjaTag
from sqlfmt.line import Line
from sqlfmt.mode import Mode
from sqlfmt.node_manager import NodeManager
from sqlfmt.token import Token, TokenType


@pytest.fixture
def node_manager(default_mode: Mode) -> NodeManager:
    return NodeManager(default_mode.dialect.case_sensitive_names)


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
    monkeypatch.setitem(sys.modules, "black", None)


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
        (
            "{% macro my_macro(arg, kwarg=foo) %}",
            ("{%", "macro ", "my_macro(arg, kwarg=foo)", "%}"),
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
    assert JinjaTag.from_string(tag, (0, 0)) == JinjaTag(tag, *result, (0, 0))


@pytest.mark.parametrize(
    "ttype,tag,formatted",
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
    jinja_formatter: JinjaFormatter,
    ttype: TokenType,
    tag: str,
    formatted: str,
    node_manager: NodeManager,
) -> None:
    t = Token(type=ttype, prefix="", token=tag, spos=0, epos=len(tag))
    n = node_manager.create_node(t, previous_node=None)
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
    disabled_jinja_formatter: JinjaFormatter,
    source_string: str,
    node_manager: NodeManager,
) -> None:
    t = Token(
        type=TokenType.JINJA_STATEMENT,
        prefix="",
        token=source_string,
        spos=0,
        epos=len(source_string),
    )
    n = node_manager.create_node(t, previous_node=None)
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
    uninstall_black: None,
    jinja_formatter: JinjaFormatter,
    source_string: str,
    node_manager: NodeManager,
) -> None:
    t = Token(
        type=TokenType.JINJA_STATEMENT,
        prefix="",
        token=source_string,
        spos=0,
        epos=len(source_string),
    )
    n = node_manager.create_node(t, previous_node=None)
    jinja_formatter._format_jinja_node(n, 88)
    assert n.value == source_string


def test_format_line(
    jinja_formatter: JinjaFormatter, node_manager: NodeManager
) -> None:
    t = Token(
        type=TokenType.JINJA_EXPRESSION,
        prefix="",
        token="{{expression}}",
        spos=0,
        epos=14,
    )
    n = node_manager.create_node(t, previous_node=None)
    line = Line.from_nodes(previous_node=None, nodes=[n], comments=[])
    node_manager.append_newline(line)

    assert n.value == "{{expression}}"
    _ = list(map(jinja_formatter.format_line, [line]))
    assert n.value == "{{ expression }}"


def test_format_line_single_to_multi(
    default_analyzer: Analyzer, jinja_formatter: JinjaFormatter
) -> None:
    source_string = (
        "from {{ source('fooooooooooooooooooooooooooooooooooooooooooooooooooo', "
        "'barrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr') }}"
    )
    q = default_analyzer.parse_query(source_string=source_string)
    assert len(q.lines) == 1
    line = q.lines[0]
    j_node = line.nodes[1]
    assert j_node.is_jinja
    assert not j_node.is_multiline_jinja

    new_lines = jinja_formatter.format_line(line)
    assert len(new_lines) == 2  # make sure the linesplitter did its thing
    assert j_node.is_multiline_jinja  # jinjafmt mutated this node to be multiline


@pytest.mark.parametrize(
    "source_string,expected_string",
    [
        ("1 +      1", "1 + 1"),
        ("'a' ~      'b'", '"a" ~ "b"'),
        ("dbt_utils.star(\nfrom=one\n)", "dbt_utils.star(from=one)"),
        ("return(\nfoo\n)", "return(foo)"),
    ],
)
def test_black_wrapper_format_string(
    source_string: str, expected_string: str, jinja_formatter: JinjaFormatter
) -> None:
    result = jinja_formatter.code_formatter.format_string(
        source_string=source_string, max_length=88
    )
    assert result == (expected_string, True)


def test_black_wrapper_format_string_no_black(
    uninstall_black: None, default_mode: Mode
) -> None:
    source_string = "1 +    1"
    jinja_formatter = JinjaFormatter(default_mode)
    result = jinja_formatter.code_formatter.format_string(
        source_string=source_string, max_length=88
    )
    assert result == (source_string, False)


@pytest.mark.parametrize(
    "source_string", [":::", ":::\n:::", "1,\n2" "return(return_())"]
)
def test_black_wrapper_format_string_invalid_input(
    source_string: str,
    jinja_formatter: JinjaFormatter,
) -> None:
    """
    Our prepocessor will abort the keyword substitution because the sentinel return_
    already exists in the source.
    """
    result = jinja_formatter.code_formatter.format_string(
        source_string=source_string, max_length=88
    )
    assert result == (source_string, False)


@pytest.mark.parametrize(
    "tag,expected",
    [
        (
            JinjaTag("{{ any code! }}", "{{", "", "any code!", "}}", (0, 0)),
            88 - 2 - 2 - 2,
        ),
        (JinjaTag("{%- set _ %}", "{%-", "set", "_", "%}", (0, 0)), 88 - 3 - 3 - 2 - 2),
    ],
)
def test_max_code_length(tag: JinjaTag, expected: int) -> None:
    result = tag.max_code_length(88)
    assert result == expected


@pytest.mark.parametrize(
    "source_string,expected_res",
    [
        ("my_macro(one, two, three='my_kwarg')", ("", (False, {}, {}))),
        ("my_macro(\n    one, two, three='my_kwarg'\n)", ("", (True, {}, {}))),
        (
            "my_macro(\n    one,\n    two,\n    three='my_kwarg',\n)",
            ("", (True, {}, {})),
        ),
        ("my_list = [\n1, 2, 3,\n]", ("", (True, {}, {}))),
        (
            "return(import(except=1))",
            (
                "return_(import_(except_=1))",
                (False, {r"return_\(": 1, r"import_\(": 1, r"except_\s*=": 1}, {}),
            ),
        ),
        ("'a' ~     'b'", ("'a' +     'b'", (False, {}, {"+": 1}))),
    ],
)
def test_preprocess_string_properties(
    source_string: str, expected_res: Tuple[str, BlackWrapper.StringProperties]
) -> None:
    res_string, res_properties = BlackWrapper._preprocess_string(source_string)
    assert res_string == expected_res[0] if expected_res[0] else source_string
    assert res_properties == expected_res[1]


@pytest.mark.parametrize(
    "source_string,expected_count,is_def",
    [
        ("{% macro my_macro(foo, bar, baz=qux) %}", 2, True),
        ("{% test my_test(foo, bar, baz=qux) %}", 2, True),
        ("{% macro my_macro(foo, bar, baz=qux,) %}", 2, True),
        ("{% test my_test(foo, bar, baz=qux,) %}", 2, True),
        ("{% macro my_macro(\n    foo,\n    bar, \n    baz=qux,\n) %}", 2, True),
        ("{% test my_test(\n    foo,\n    bar, \n    baz=qux,\n) %}", 2, True),
        ("{% materialization my_mat, default %}", 1, True),
        ("{% call statement('foo', fetch_results=True, auto_begin=True) %}", 2, True),
        # do not remove from macro calls, only defs
        ("{{ my_macro(\n    foo,\n    bar, \n    baz=qux,\n) }}", 3, False),
    ],
)
def test_jinja_tag_remove_trailing_comma(
    source_string: str, expected_count: int, is_def: bool
) -> None:
    tag = JinjaTag.from_string(source_string=source_string, depth=(0, 0))
    assert tag.is_macro_like_def == is_def
    tag.is_blackened = True
    result = str(tag)
    assert result.count(",") == expected_count


@pytest.mark.parametrize(
    "source_string,expected_string,expected_kw_replacements",
    [
        (
            "return(adapter.dispatch('my_macro', 'my_package')(arg1, arg2))",
            "return_(adapter.dispatch('my_macro', 'my_package')(arg1, arg2))",
            {r"return_\(": 1},
        ),
        (
            "dbt_utils.star(from=ref('asdf'), except=fields_to_exclude)",
            "dbt_utils.star(from_=ref('asdf'), except_=fields_to_exclude)",
            {r"from_\s*=": 1, r"except_\s*=": 1},
        ),
        (
            "True = foo",
            "True_= foo",
            {r"True_\s*=": 1},
        ),
        (
            "abc = True",
            "abc = True",
            {},
        ),
        (
            "if foo == 'bar'",
            "if foo == 'bar'",
            {},
        ),
        (
            "from_ = 'already there'",
            "from_ = 'already there'",
            {},
        ),
        (
            "from_ = from()",
            "from_ = from_()",
            {r"from_\(": 1},
        ),
        (
            "return(from_())",
            "return_(from_())",
            {r"return_\(": 1},
        ),
    ],
)
def test_replace_reserved_words(
    source_string: str, expected_string: str, expected_kw_replacements: Dict[str, int]
) -> None:
    processed_string, actual_kw_replacements = BlackWrapper._replace_reserved_words(
        source_string=source_string
    )
    assert processed_string == expected_string
    assert actual_kw_replacements == expected_kw_replacements


@pytest.mark.parametrize(
    "source_string",
    [
        "from_ = (from == 1)",
        "return(return_())",
    ],
)
def test_replace_reserved_words_preexisting_sentinels(source_string: str) -> None:
    with pytest.raises(ValueError):
        _, _ = BlackWrapper._replace_reserved_words(source_string=source_string)


@pytest.mark.parametrize(
    "source_string,expected_string,expected_tilde_replacements",
    [
        ('"a" ~ "b"', '"a" + "b"', {"+": 1}),
        ('"a" ~ "b" + 1', '"a" - "b" + 1', {"-": 1}),
        ('"a" ~ "b" - 1', '"a" + "b" - 1', {"+": 1}),
        ("foo", "foo", {}),
        ("foo + bar", "foo + bar", {}),
        ("~+-*/", "~+-*/", {}),
        ("foo ~ bar + baz - qux * foo / bar", "foo ~ bar + baz - qux * foo / bar", {}),
    ],
)
def test_replace_tildes(
    source_string: str,
    expected_string: str,
    expected_tilde_replacements: Dict[str, int],
) -> None:
    processed_string, actual_tilde_replacements = BlackWrapper._replace_tildes(
        source_string=source_string
    )
    assert processed_string == expected_string
    assert actual_tilde_replacements == expected_tilde_replacements


@pytest.mark.parametrize(
    "formatted_string,keyword_replacements,tilde_replacements,expected_string",
    [
        (
            "from_ = 'already there'",
            {},
            {},
            "from_ = 'already there'",
        ),
        (
            "from_ = 'replaced a keyword'",
            {r"from_\s*=": 1},
            {},
            "from = 'replaced a keyword'",
        ),
        (
            "dbt_utils.star(from_=ref('asdf'), except_=fields_to_exclude)",
            {r"from_\s*=": 1, r"except_\s*=": 1},
            {},
            "dbt_utils.star(from=ref('asdf'), except=fields_to_exclude)",
        ),
        ("foo + bar", {}, {"+": 1}, "foo ~ bar"),
        ("foo + bar / baz", {}, {"/": 1}, "foo + bar ~ baz"),
        ("foo + bar", {}, {}, "foo + bar"),
    ],
)
def test_postprocess_string(
    formatted_string: str,
    keyword_replacements: Dict[str, int],
    tilde_replacements: Dict[str, int],
    expected_string: str,
) -> None:
    processed_string = BlackWrapper._postprocess_string(
        formatted_string,
        string_properties=BlackWrapper.StringProperties(
            has_newlines=False,
            keyword_replacements=keyword_replacements,
            tilde_replacements=tilde_replacements,
        ),
    )
    assert processed_string == expected_string


@pytest.mark.parametrize(
    "source_string",
    BlackWrapper.PY_RESERVED_WORDS
    + [
        "dbt_utils.star(from=ref('asdf'), except=fields_to_exclude)",
        "return(adapter.dispatch('my_macro', 'my_package')(arg1, arg2))",
        "True = foo",
        "abc = True",
        "something if something_else",
        "foo ~ bar",
    ],
)
def test_preprocess_and_postprocess_are_inverse_ops(source_string: str) -> None:
    """
    Preprocess and Postprocess should be perfectly inverse operations, except
    for some whitespace (we don't need to be too precious about whitespace because
    in the app Black will run between pre and post processing)
    """
    assert BlackWrapper._postprocess_string(
        *BlackWrapper._preprocess_string(source_string)
    ).replace(" ", "") == source_string.replace(" ", "")


@pytest.mark.parametrize(
    "source_string",
    [
        """{{\n    config(\n        foo="bar",\n    )\n}}""",
        '''{{\n    config(\n        foo="""\n\nbar\n\n""",\n    )\n}}''',
    ],
)
def test_multiline_str(source_string: str) -> None:
    tag = JinjaTag.from_string(source_string=source_string, depth=(0, 0))
    tag.code, tag.is_blackened = BlackWrapper().format_string(
        source_string=tag.code, max_length=88
    )
    assert tag.is_blackened
    assert str(tag) == source_string
