from typing import List

import pytest

from sqlfmt.comment import Comment
from sqlfmt.node import Node
from sqlfmt.node_manager import NodeManager
from sqlfmt.token import Token, TokenType


@pytest.fixture
def short_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="-- short comment", spos=0, epos=16
    )
    comment = Comment(t, is_standalone=False, previous_node=None)
    return comment


@pytest.fixture
def short_mysql_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="# short comment", spos=0, epos=15
    )
    comment = Comment(t, is_standalone=False, previous_node=None)
    return comment


@pytest.fixture
def short_js_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="// short comment", spos=0, epos=16
    )
    comment = Comment(t, is_standalone=False, previous_node=None)
    return comment


@pytest.fixture
def nospace_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="--short comment", spos=0, epos=15
    )
    comment = Comment(t, is_standalone=False, previous_node=None)
    return comment


@pytest.fixture
def standalone_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="-- short comment", spos=0, epos=16
    )
    comment = Comment(t, is_standalone=True, previous_node=None)
    return comment


@pytest.fixture
def multiline_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="/*\ncomment\n*/", spos=0, epos=15
    )
    comment = Comment(t, is_standalone=True, previous_node=None)
    return comment


@pytest.fixture
def datbricks_query_hint_comment() -> Comment:
    n = Node(
        Token(
            type=TokenType.UNTERM_KEYWORD,
            prefix="",
            token="select",
            spos=0,
            epos=6,
        ),
        previous_node=None,
        prefix="",
        value="select",
        open_brackets=[],
        open_jinja_blocks=[],
        formatting_disabled=[],
    )
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="/*+ hint here */", spos=6, epos=23
    )
    comment = Comment(t, is_standalone=False, previous_node=n)
    return comment


@pytest.fixture
def fmt_disabled_comment() -> Comment:
    t = Token(type=TokenType.FMT_OFF, prefix="", token="--fmt: off", spos=0, epos=10)
    mgr = NodeManager(case_sensitive_names=False)
    node = mgr.create_node(t, None)
    ct = Token(
        type=TokenType.COMMENT,
        prefix="          ",
        token="--   comment",
        spos=11,
        epos=33,
    )
    comment = Comment(ct, is_standalone=True, previous_node=node)
    return comment


def test_get_marker(
    short_comment: Comment,
    short_mysql_comment: Comment,
    nospace_comment: Comment,
    short_js_comment: Comment,
    datbricks_query_hint_comment: Comment,
) -> None:
    assert short_comment._get_marker() == ("--", 3)
    assert short_mysql_comment._get_marker() == ("#", 2)
    assert short_js_comment._get_marker() == ("//", 3)
    assert nospace_comment._get_marker() == ("--", 2)
    assert datbricks_query_hint_comment._get_marker() == ("/*", 2)


def test_comment_parts(
    short_comment: Comment,
    short_mysql_comment: Comment,
    nospace_comment: Comment,
    short_js_comment: Comment,
) -> None:
    assert short_comment._comment_parts() == ("--", "short comment")
    assert short_mysql_comment._comment_parts() == ("#", "short comment")
    assert short_js_comment._comment_parts() == ("--", "short comment")
    assert nospace_comment._comment_parts() == ("--", "short comment")


def test_str_len(
    short_comment: Comment,
    short_mysql_comment: Comment,
    nospace_comment: Comment,
    short_js_comment: Comment,
) -> None:
    assert str(short_comment) == short_comment.token.token
    assert str(short_mysql_comment) == short_mysql_comment.token.token
    assert str(short_js_comment) == f"-- {short_js_comment.body}"
    assert str(nospace_comment) == str(short_comment)

    assert len(short_comment) == 16
    assert len(short_mysql_comment) == 15
    assert len(short_js_comment) == 16
    assert len(nospace_comment) == 16


def test_render_inline(
    short_comment: Comment,
    nospace_comment: Comment,
    short_js_comment: Comment,
) -> None:
    expected = "  -- short comment"
    assert short_comment.render_inline() == expected
    assert short_js_comment.render_inline() == expected
    assert nospace_comment.render_inline() == expected


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        " " * 4,
    ],
)
def test_render_standalone(short_comment: Comment, prefix: str) -> None:
    assert (
        short_comment.render_standalone(max_length=88, prefix=prefix)
        == prefix + str(short_comment) + "\n"
    )
    wrapped_comment = short_comment.render_standalone(max_length=14, prefix=prefix)
    lines = wrapped_comment.splitlines(keepends=True)
    assert lines[0] == prefix + "-- short\n"
    assert lines[1] == prefix + "-- comment\n"


def test_render_standalone_formatting_disabled(fmt_disabled_comment: Comment) -> None:
    assert (
        fmt_disabled_comment.render_standalone(max_length=88, prefix="")
        == f"{fmt_disabled_comment.token.prefix}{fmt_disabled_comment.token.token}\n"
    )


def test_render_standalone_wrap_strip_whitespace() -> None:
    txt = "-- foo" + " " * 100 + "bar"
    t = Token(type=TokenType.COMMENT, prefix="", token=txt, spos=0, epos=len(txt))
    comment = Comment(t, is_standalone=True, previous_node=None)
    assert comment.render_standalone(max_length=88, prefix="") == "-- foo\n-- bar\n"


def test_render_multiline(multiline_comment: Comment) -> None:
    assert str(multiline_comment) == "/*\ncomment\n*/"
    assert (
        multiline_comment.render_standalone(max_length=88, prefix="")
        == f"{multiline_comment}\n"
    )


@pytest.mark.parametrize(
    "text,expected_splits",
    [
        ("asdf", ["asdf"]),
        ("asdfqwerzxcv", ["asdfqwerzxcv"]),
        ("asdf qwer", ["asdf qwer"]),
        ("asdf qwer zxcv", ["asdf qwer", "zxcv"]),
        ("asdf qwer zxcv uiophjkl vbnm", ["asdf qwer", "zxcv", "uiophjkl", "vbnm"]),
    ],
)
def test_split_before(text: str, expected_splits: List[str]) -> None:
    result = list(Comment._split_before(text, max_length=10))
    assert result == expected_splits


def test_empty_comment() -> None:
    t = Token(type=TokenType.COMMENT, prefix=" ", token="-- ", spos=0, epos=3)
    comment = Comment(t, is_standalone=True, previous_node=None)
    assert str(comment) == "--"


def test_is_inline(
    short_comment: Comment, standalone_comment: Comment, multiline_comment: Comment
) -> None:
    assert short_comment.is_inline
    assert not (standalone_comment.is_inline)
    assert not (multiline_comment.is_inline)


def test_no_wrap_long_jinja_comments() -> None:
    comment_str = "{# " + ("comment " * 20) + "#}"
    t = Token(
        type=TokenType.COMMENT,
        prefix=" ",
        token=comment_str,
        spos=0,
        epos=len(comment_str),
    )
    comment = Comment(t, is_standalone=True, previous_node=None)
    rendered = comment.render_standalone(88, "")

    assert rendered == comment_str + "\n"


def test_no_add_space_databricks_hint(datbricks_query_hint_comment: Comment) -> None:
    assert str(datbricks_query_hint_comment) == datbricks_query_hint_comment.token.token
