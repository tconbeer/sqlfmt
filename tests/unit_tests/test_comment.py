from typing import List

import pytest

from sqlfmt.comment import Comment
from sqlfmt.exception import InlineCommentException
from sqlfmt.token import Token, TokenType


@pytest.fixture
def short_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="-- short comment", spos=0, epos=16
    )
    comment = Comment(t, is_standalone=False)
    return comment


@pytest.fixture
def short_mysql_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="# short comment", spos=0, epos=15
    )
    comment = Comment(t, is_standalone=False)
    return comment


@pytest.fixture
def nospace_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="--short comment", spos=0, epos=15
    )
    comment = Comment(t, is_standalone=False)
    return comment


@pytest.fixture
def standalone_comment() -> Comment:
    t = Token(
        type=TokenType.COMMENT, prefix=" ", token="-- short comment", spos=0, epos=16
    )
    comment = Comment(t, is_standalone=True)
    return comment


def test_get_marker(
    short_comment: Comment, short_mysql_comment: Comment, nospace_comment: Comment
) -> None:
    assert short_comment._get_marker() == ("--", 3)
    assert short_mysql_comment._get_marker() == ("#", 2)
    assert nospace_comment._get_marker() == ("--", 2)


def test_comment_parts(
    short_comment: Comment, short_mysql_comment: Comment, nospace_comment: Comment
) -> None:
    assert short_comment._comment_parts() == ("--", "short comment")
    assert short_mysql_comment._comment_parts() == ("#", "short comment")
    assert nospace_comment._comment_parts() == ("--", "short comment")


def test_str_len(
    short_comment: Comment, short_mysql_comment: Comment, nospace_comment: Comment
) -> None:
    assert str(short_comment) == short_comment.token.token + "\n"
    assert str(short_mysql_comment) == short_mysql_comment.token.token + "\n"
    assert str(nospace_comment) == str(short_comment)

    assert len(short_comment) == 17
    assert len(short_mysql_comment) == 16
    assert len(nospace_comment) == 17


def test_render_inline(
    short_comment: Comment, nospace_comment: Comment, standalone_comment: Comment
) -> None:
    expected = "  -- short comment\n"
    assert short_comment.render_inline(max_length=88, content_length=20) == expected
    assert nospace_comment.render_inline(max_length=88, content_length=20) == expected
    with pytest.raises(InlineCommentException):
        # can't inline a standalone comment
        assert standalone_comment.render_inline(max_length=88, content_length=20)

    with pytest.raises(InlineCommentException):
        # can't inline if the content is too long
        assert short_comment.render_inline(max_length=88, content_length=80)


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        " " * 4,
    ],
)
def test_render_standalone(short_comment: Comment, prefix: str) -> None:
    assert short_comment.render_standalone(
        max_length=88, prefix=prefix
    ) == prefix + str(short_comment)
    wrapped_comment = short_comment.render_standalone(max_length=14, prefix=prefix)
    lines = wrapped_comment.splitlines(keepends=True)
    assert lines[0] == prefix + "-- short\n"
    assert lines[1] == prefix + "-- comment\n"


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
    comment = Comment(t, is_standalone=True)
    assert str(comment) == "--\n"
