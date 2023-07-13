import re
from dataclasses import dataclass
from typing import ClassVar, Iterator, Optional, Tuple

from sqlfmt.node import Node
from sqlfmt.token import Token, TokenType


@dataclass
class Comment:
    """
    A Comment wraps a token (of type COMMENT), and provides a number of properties and
    methods that are used in formatting and printing the query
    """

    token: Token
    is_standalone: bool
    previous_node: Optional[Node]
    comment_marker: ClassVar[re.Pattern] = re.compile(r"(--|#|/\*|\{#-?)([^\S\n]*)")

    def __str__(self) -> str:
        """
        Returns the contents of the comment token plus a trailing newline,
        without preceding whitespace, with a single space between the marker
        and the comment text.
        """
        if self.is_multiline or self.formatting_disabled:
            return f"{self.token.token}"
        else:
            marker, comment_text = self._comment_parts()
            if comment_text:
                return f"{marker} {comment_text}"
            else:
                return f"{marker}"

    def __len__(self) -> int:
        return len(str(self))

    def _get_marker(self) -> Tuple[str, int]:
        """
        For a comment, returns a tuple.

        The first element is the comment's marker, which is the symbol or symbols
        that indicates that the rest of the token is a comment; e.g., "--" or "#"

        The second element is the position of the comment's text, which is the
        first non-whitespace character after the marker
        """
        match = self.comment_marker.match(self.token.token)
        assert match, f"{self.token.token} does not match comment marker"
        _, epos = match.span(1)
        _, len = match.span(2)
        return self.token.token[:epos], len

    def _comment_parts(self) -> Tuple[str, str]:
        """
        For a comment, returns a tuple of the comment's marker and its contents
        (without leading whitespace)
        """
        assert not self.is_multiline
        marker, skipchars = self._get_marker()
        comment_text = self.token.token[skipchars:]
        return marker, comment_text

    @property
    def is_multiline(self) -> bool:
        """
        Returns True if this Comment contains newlines
        """
        return "\n" in self.token.token

    @property
    def is_c_style(self) -> bool:
        return self.token.token.startswith("/*")

    @property
    def is_inline(self) -> bool:
        return not self.is_standalone and not self.is_multiline and not self.is_c_style

    @property
    def formatting_disabled(self) -> bool:
        if self.previous_node is None:
            return False
        else:
            # comment formatting is only disabled if there is an explicit FMT_OFF token
            # (i.e., not if node formatting is disabled due to DATA nodes).
            return any(
                [
                    t.type is TokenType.FMT_OFF
                    for t in self.previous_node.formatting_disabled
                ]
            )

    def render_inline(self) -> str:
        """
        Renders a comment as an inline comment, assuming it'll fit.
        """
        prefix = self.token.prefix if self.formatting_disabled else "  "
        return f"{prefix}{self}"

    def render_standalone(self, max_length: int, prefix: str) -> str:
        """
        For a Comment, returns the string for properly formatting this Comment
        as a standalone comment (on its own line)
        """
        if self.formatting_disabled:
            rendered = f"{self.token.prefix}{self}"
        elif self.is_multiline:
            # todo: split lines, indent each line the same
            rendered = prefix + str(self)
        else:
            if len(self) + len(prefix) <= max_length:
                rendered = prefix + str(self)
            else:
                marker, comment_text = self._comment_parts()
                if marker in ("--", "#"):
                    available_length = max_length - len(prefix) - len(marker) - 2
                    line_gen = self._split_before(comment_text, available_length)
                    rendered = "".join(
                        [prefix + marker + " " + txt.strip() + "\n" for txt in line_gen]
                    )
                else:  # block-style or jinja comment. Don't wrap long lines for now
                    rendered = prefix + str(self)
        nl = "\n"
        return f"{rendered.rstrip(nl)}\n"

    @classmethod
    def _split_before(cls, text: str, max_length: int) -> Iterator[str]:
        """
        When rendering very long comments, we try to split them at the desired line
        length and wrap them onto multiple lines. This method takes the contents of
        a comment (without the marker) and a maximum length, and splits the original
        text at whitespace, yielding each split as a stringd
        """
        if len(text) < max_length:
            yield text.rstrip()
        else:
            for idx, char in enumerate(reversed(text[:max_length])):
                if char.isspace():
                    yield text[: max_length - idx].rstrip()
                    yield from cls._split_before(text[max_length - idx :], max_length)
                    break
            else:  # no spaces in the comment
                yield text.rstrip()
