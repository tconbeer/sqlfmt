from dataclasses import dataclass
from typing import List, Tuple

from sqlfmt.comment import Comment
from sqlfmt.line import Line
from sqlfmt.node import Node
from sqlfmt.node_manager import NodeManager


@dataclass
class LineSplitter:
    node_manager: NodeManager

    def maybe_split(self, line: Line) -> List[Line]:
        """
        Evaluates a line for splitting. If line matches criteria for splitting,
        returns a list of new lines; otherwise returns a list of only the original line.

        We used to do this recursively, but very long lines (with >500 splits) would
        raise RecursionError.
        """

        if line.formatting_disabled:
            return [line]

        new_lines: List[Line] = []
        comments = line.comments
        head = 0
        always_split_after = never_split_after = False
        for i, node in enumerate(line.nodes):
            if node.is_newline:
                if head == 0:
                    new_lines.append(line)
                else:
                    new_line, comments = self.split_at_index(
                        line, head, i, comments, no_tail=True
                    )
                    assert (
                        not comments
                    ), "Comments must be empty here or we'll drop them"
                    new_lines.append(new_line)
                return new_lines
            elif (
                i > head
                and not never_split_after
                and not node.formatting_disabled
                and (always_split_after or self.maybe_split_before(node))
            ):
                new_line, comments = self.split_at_index(line, head, i, comments)
                new_lines.append(new_line)
                head = i
                # node now follows a new newline node, so we need to update
                # its previous node (this can impact its depth)
                node.previous_node = new_line.nodes[-1]

            always_split_after, never_split_after = self.maybe_split_after(node)

        new_line, comments = self.split_at_index(line, head, -1, comments, no_tail=True)
        assert not comments, "Comments must be empty here or we'll drop them"
        new_lines.append(new_line)
        return new_lines

    def maybe_split_before(self, node: Node) -> bool:
        """
        Return True if we should split before node
        """
        if (
            # if there is a multiline node on this line and it isn't the
            # only thing on this line, then split before the multiline node
            node.is_multiline_jinja
            # always split before any unterm kw
            or node.is_unterm_keyword
            # always split before any opening jinja block
            or node.is_opening_jinja_block
            # always split before operators
            or node.is_operator
            # always split before any node that decreases depth
            or node.is_closing_bracket
            or node.is_closing_jinja_block
            # always split before a node that divides queries
            or node.divides_queries
        ):
            return True
        # split if an opening bracket immediately follows
        # a closing bracket
        elif self.maybe_split_between_brackets(node):
            return True
        else:
            return False

    def maybe_split_between_brackets(self, node: Node) -> bool:
        """
        Return true if this is an open bracket that follows
        a closing bracket. This is typically for BQ
        array indexing, like split(my_field)[offset(1)],
        or dictionary accessing, like my_json['outer']['inner']
        """
        return (
            node.is_opening_bracket
            and node.previous_node is not None
            and node.previous_node.is_closing_bracket
        )

    def maybe_split_after(self, node: Node) -> Tuple[bool, bool]:
        """
        Return True, False if we should always split after node
        Retrun False, True if we should never split after node
        Return False, False if splitting after should depend on the
        contents of the next node
        """
        if (
            # always split after any comma that doesn't end a line
            node.is_comma
            # always split after a token that increases depth
            or node.is_opening_bracket
            or node.is_opening_jinja_block
            or node.is_unterm_keyword
            # always split after a token that divides queries
            or node.divides_queries
        ):
            return True, False
        elif node.formatting_disabled:
            return False, True
        else:
            return False, False

    def split_at_index(
        self,
        line: Line,
        head: int,
        index: int,
        comments: List[Comment],
        no_tail: bool = False,
    ) -> Tuple[Line, List[Comment]]:
        """
        Return a new line comprised of the nodes line[head:index], plus a newline node.

        Also return a list of comments that need to be included in the tail
        of the split line. This includes inline comments and if the head
        is just a comma, all comments.
        """
        if index == -1:
            new_nodes = line.nodes[head:]
        else:
            assert index > head, "Cannot split at start of line!"
            new_nodes = line.nodes[head:index]

        assert new_nodes, "Cannot split a line without nodes!"

        if no_tail:
            head_comments, tail_comments = comments, []

        elif comments:
            if new_nodes[0].is_comma:
                head_comments, tail_comments = [], comments
            elif index == len(line.nodes) - 2 and line.nodes[index].is_operator:
                # the only thing after the split is an operator + \n, so keep the
                # comments with the stuff before the operator
                head_comments, tail_comments = comments, []
            else:
                head_comments, tail_comments = [], []
                for comment in comments:
                    if (
                        comment.is_standalone
                        or comment.is_multiline
                        or comment.previous_node is None
                    ):
                        head_comments.append(comment)
                    elif comment.is_inline:
                        tail_comments.append(comment)
                    elif comment.is_c_style and comment.previous_node in new_nodes:
                        head_comments.append(comment)
                    else:
                        tail_comments.append(comment)

        else:  # no comments
            head_comments, tail_comments = [], []

        new_line = Line.from_nodes(
            previous_node=new_nodes[0].previous_node,
            nodes=new_nodes,
            comments=head_comments,
        )
        if not new_line.nodes[-1].is_newline:
            self.node_manager.append_newline(new_line)

        return new_line, tail_comments
