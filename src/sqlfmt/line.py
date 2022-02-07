import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from sqlfmt.comment import Comment
from sqlfmt.exception import InlineCommentException
from sqlfmt.node import Node
from sqlfmt.token import Token, TokenType

if sys.version_info >= (3, 8):
    from functools import cached_property
else:
    from backports.cached_property import cached_property


@dataclass
class Line:
    """
    A Line is a collection of Nodes and Comments that should be printed together, on a
    single line.
    """

    previous_node: Optional[Node]  # last node of prior line, if any
    nodes: List[Node] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    formatting_disabled: bool = False

    def __str__(self) -> str:
        return self._calc_str

    @cached_property
    def _calc_str(self) -> str:
        """
        A Line is printed in one of three ways:
        1. Blank lines are just bare newlines, with no other whitespace
        2. Lines where formatting is disabled must use the original lexed token,
           and print exactly what we lexed
        3. Concatenate all Nodes and prepend the correct amount of whitespace
           for indentation

        Does not include any Comments; for those, use the render_with_comments
        method

        Cached for performance.
        """
        if self.is_blank_line:
            return "\n"
        elif self.formatting_disabled:
            return "".join([f"{t.prefix}{t.token}" for t in self.tokens])
        else:
            return self.prefix + "".join([str(node) for node in self.nodes]).lstrip(" ")

    def __len__(self) -> int:
        try:
            return max([len(s) for s in str(self).splitlines()])
        except ValueError:
            return 0

    @property
    def open_brackets(self) -> List[Node]:
        """
        The brackets open at the start of this Line
        """
        if self.nodes:
            return self.nodes[0].open_brackets
        elif self.previous_node:
            return self.previous_node.open_brackets
        else:
            return []

    @property
    def open_jinja_blocks(self) -> List[Node]:
        """
        The jinja blocks open at the start of this Line
        """
        if self.nodes:
            return self.nodes[0].open_jinja_blocks
        elif self.previous_node:
            return self.previous_node.open_jinja_blocks
        else:
            return []

    @property
    def depth(self) -> Tuple[int, int]:
        """
        The depth of the start of this line
        """
        if self.nodes:
            return (len(self.open_brackets), len(self.open_jinja_blocks))
        else:
            return (0, 0)

    @property
    def prefix(self) -> str:
        """
        Returns the whitespace to be printed at the start of this Line for
        proper indentation.
        """
        INDENT = " " * 4
        prefix = INDENT * self.depth[0]
        return prefix

    def render_with_comments(self, max_length: int) -> str:
        """
        Returns a string that represents the properly-formatted Line,
        including associated comments
        """
        content = str(self)
        rendered = content
        if len(self.comments) == 1:
            # standalone or multiline comment
            if self.nodes[0].is_newline:
                rendered = f"{self.prefix}{self.comments[0]}"
            # inline comment
            else:
                try:
                    comment = self.comments[0].render_inline(
                        max_length=max_length, content_length=len(content.rstrip())
                    )
                    rendered = f"{content.rstrip()}{comment}"
                except InlineCommentException:
                    comment = self.comments[0].render_standalone(
                        max_length=max_length, prefix=self.prefix
                    )
                    rendered = f"{comment}{content}"
        # wrap comments above; note that str(comment) is newline-terminated
        elif len(self.comments) > 1:
            comment = "".join(
                [
                    c.render_standalone(max_length=max_length, prefix=self.prefix)
                    for c in self.comments
                ]
            )
            rendered = f"{comment}{content}"
        return rendered

    def append_token(self, token: Token) -> None:
        """
        Creates a new Node from the passed token and the context of the current line,
        then appends that Node to self.nodes and updates line depth and split features
        as necessary
        """
        previous_node: Optional[Node]
        if self.nodes:
            previous_node = self.nodes[-1]
        else:
            previous_node = self.previous_node

        node = Node.from_token(token, previous_node)

        self.formatting_disabled = self.formatting_disabled or node.formatting_disabled

        self.nodes.append(node)

    def append_newline(self) -> None:
        """
        Create a new NEWLINE token and append it to the end of this line
        """
        previous_token: Optional[Token] = None
        if self.nodes:
            previous_token = self.nodes[-1].token
        elif self.previous_node:
            previous_token = self.previous_node.token

        if previous_token:
            spos = previous_token.epos
            epos = spos
        else:
            spos = 0
            epos = 0

        nl = Token(
            type=TokenType.NEWLINE,
            prefix="",
            token="\n",
            spos=spos,
            epos=epos,
        )
        self.append_token(nl)

    @classmethod
    def from_nodes(
        cls,
        previous_node: Optional[Node],
        nodes: List[Node],
        comments: List[Comment],
    ) -> "Line":
        """
        Creates and returns a new line from a list of Nodes. Useful for line
        splitting and merging
        """
        if nodes:
            nodes[0].previous_node = previous_node
            line = Line(
                previous_node=previous_node,
                nodes=nodes,
                comments=comments,
                formatting_disabled=nodes[0].formatting_disabled
                or nodes[-1].formatting_disabled,
            )
        else:
            line = Line(
                previous_node=previous_node,
                nodes=nodes,
                comments=comments,
                formatting_disabled=previous_node.formatting_disabled
                if previous_node
                else False,
            )

        return line

    @property
    def tokens(self) -> List[Token]:
        tokens = []
        for node in self.nodes:
            tokens.append(node.token)
        return tokens

    @cached_property
    def is_blank_line(self) -> bool:
        if (
            len(self.nodes) == 1
            and self.nodes[0].is_newline
            and len(self.comments) == 0
        ):
            return True
        else:
            return False

    @property
    def starts_with_unterm_keyword(self) -> bool:
        try:
            return self.nodes[0].is_unterm_keyword
        except IndexError:
            return False

    @property
    def starts_with_operator(self) -> bool:
        try:
            return self.nodes[0].is_operator
        except IndexError:
            return False

    @property
    def starts_with_low_priority_merge_operator(self) -> bool:
        try:
            return self.nodes[0].is_low_priority_merge_operator
        except IndexError:
            return False

    @property
    def starts_with_comma(self) -> bool:
        try:
            return self.nodes[0].is_comma
        except IndexError:
            return False

    @property
    def contains_unterm_keyword(self) -> bool:
        return any([n.is_unterm_keyword for n in self.nodes])

    @property
    def contains_operator(self) -> bool:
        return any([n.is_operator for n in self.nodes])

    @cached_property
    def contains_jinja(self) -> bool:
        return any([n.is_jinja for n in self.nodes])

    @property
    def contains_multiline_node(self) -> bool:
        return any([n.is_multiline for n in self.nodes])

    @property
    def is_standalone_multiline_node(self) -> bool:
        if len(self.nodes) == 1 and self.contains_multiline_node:
            return True
        if (
            len(self.nodes) == 2
            and self.contains_multiline_node
            and self.nodes[-1].is_newline
        ):
            return True
        else:
            return False

    @property
    def is_standalone_jinja_statement(self) -> bool:
        if len(self.nodes) == 1 and self.nodes[0].is_jinja_statement:
            return True
        if (
            len(self.nodes) == 2
            and self.nodes[0].is_jinja_statement
            and self.nodes[1].is_newline
        ):
            return True
        else:
            return False

    @property
    def is_standalone_operator(self) -> bool:
        if len(self.nodes) == 1 and self.starts_with_operator:
            return True
        if (
            len(self.nodes) == 2
            and self.starts_with_operator
            and self.nodes[1].is_newline
        ):
            return True
        else:
            return False

    def is_too_long(self, max_length: int) -> bool:
        """
        Returns true if the rendered length of the line is strictly greater
        than max_length, and if the line isn't a standalone long
        multiline node
        """
        if len(self) > max_length:
            return True
        else:
            return False

    @property
    def closes_bracket_from_previous_line(self) -> bool:
        """
        Returns true for a line with an explicit bracket like ")" or "]"
        that matches a bracket on a preceding line. False for unterminated
        keywords or any lines with matched brackets
        """
        if self.previous_node and self.previous_node.open_brackets and self.nodes:
            explicit_brackets = [
                b for b in self.previous_node.open_brackets if b.is_opening_bracket
            ]
            if (
                explicit_brackets
                and explicit_brackets[-1] not in self.nodes[-1].open_brackets
            ):
                return True
        return False

    @property
    def previous_line_has_open_jinja_blocks_not_keywords(self) -> bool:
        """
        Returns true if the previous line is inside a jinja block, but not
        after a jinja block keyword, like {% else %}/{% elif %}
        """
        if (
            self.previous_node
            and self.previous_node.open_jinja_blocks
            and not self.previous_node.open_jinja_blocks[-1].is_jinja_block_keyword
        ):
            return True
        else:
            return False

    @property
    def closes_jinja_block_from_previous_line(self) -> bool:
        """
        Returns true for a line that contains {% endif %}, {% endfor %}, etc.
        where the matching {% if %}, etc. is on a previous line.
        """
        if (
            self.nodes
            and self.previous_node
            and self.previous_node.open_jinja_blocks
            and (
                self.previous_node.open_jinja_blocks[-1]
                not in self.nodes[-1].open_jinja_blocks
            )
            and (
                self.nodes[-1].open_jinja_blocks == []
                or not self.nodes[-1].open_jinja_blocks[-1].is_jinja_block_keyword
            )
        ):
            return True
        return False

    @property
    def closes_simple_jinja_block_from_previous_line(self) -> bool:
        """
        Returns true for a line that contains {% endif %}, {% endfor %}, etc.
        where the matching {% if %}, etc. is on a previous line. Returns False
        for {% else %}/{% elif %} or an {% endif %} that follows an {% else %}/
        {% endif %}
        """
        if (
            self.previous_line_has_open_jinja_blocks_not_keywords
            and self.closes_jinja_block_from_previous_line
        ):
            return True
        return False

    @property
    def opens_new_bracket(self) -> bool:
        """
        Returns True iff the Nodes in this Line open a new explicit bracket and do
        not also close that bracket
        """
        if not self.nodes:
            return False
        elif not self.nodes[-1].open_brackets:
            return False
        else:
            b = self.nodes[-1].open_brackets[-1]
            if b.is_opening_bracket and b not in self.open_brackets:
                return True
            else:
                return False
