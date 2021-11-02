from dataclasses import dataclass
from typing import List, Optional

from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode
from sqlfmt.token import TokenType


class CannotMergeException(Exception):
    pass


@dataclass
class LineMerger:
    mode: Mode

    @classmethod
    def create_merged_line(
        cls,
        lines: List[Line],
        parent_idx: int,
        child_idx: int,
    ) -> Line:
        """
        Returns a new line by merging together all nodes in the slice of lines
        from parent_idx to child_idx. Raises an exception if attempting to
        merge one line, or if the returned line would be empty or would attempt
        to merge a multiline token.
        """

        # if the child is just one below the parent, we're trying to
        # merge a single line.
        if child_idx - parent_idx == 1:
            raise CannotMergeException("Can't merge just one line")

        parent_line = lines[parent_idx]
        content_nodes: List[Node] = []
        comment_nodes: List[Node] = []

        for line in lines[parent_idx:child_idx]:
            # skip over nodes containing NEWLINEs
            nodes = [
                node
                for node in line.nodes
                if node.token.type != TokenType.NEWLINE
                and node.token.type != TokenType.COMMENT
            ]
            content_nodes.extend(nodes)
            comments = [
                node for node in line.nodes if node.token.type == TokenType.COMMENT
            ]
            comment_nodes.extend(comments)
        merged_nodes = content_nodes + comment_nodes

        if not merged_nodes:
            raise CannotMergeException("Can't merge only whitespace/newlines")
        elif any([n.is_multiline for n in merged_nodes]):
            raise CannotMergeException("Can't merge lines containing multiline nodes")

        merged_line = Line.from_nodes(
            source_string=parent_line.source_string,
            previous_node=parent_line.previous_node,
            nodes=merged_nodes,
        )

        merged_line.append_newline()

        return merged_line

    def maybe_merge_lines(self, lines: List[Line], from_depth: int = 0) -> List[Line]:
        """
        Mutates lines by combining lines if possible.

        Every time the next line indents, there is an opportunity to
        merge, by scanning the lines until the current depth
        is reached again. We do this recursively, by calling this
        method again, with a copied slice of lines
        """
        if len(lines) == 1:
            return lines

        # scan for suitable parents. Parents must have a change in depth > 0
        # before merging
        scanner = enumerate(lines)
        for parent_idx, parent_line in scanner:
            parent_depth = parent_line.depth
            if parent_line.change_in_depth < 0 or parent_depth < from_depth:
                break
            if parent_line.change_in_depth > 0:

                # scan ahead until we get back to this depth, or hit EOF.
                # note that we're using the same generator as parent loop.
                # initialize child values in case we've exhausted scanner
                child_line: Optional[Line]
                child_idx = parent_idx
                child_depth = parent_depth
                for child_idx, child_line in scanner:
                    child_depth = child_line.depth
                    if child_depth == parent_depth:
                        if (
                            parent_line.starts_with_select
                            and child_line.starts_with_unterm_keyword
                        ):
                            # this is a special case where we might be merging
                            # into a one-line select statement. In that case,
                            # we keep scanning. Otherwise, we're done.
                            pass
                        else:
                            break
                    elif child_depth < parent_depth:
                        break

                    # if we hit another indent, recursively try to merge the children
                    # of this line first, before continuing
                    if child_line.change_in_depth > 0:
                        lines[child_idx:] = self.maybe_merge_lines(
                            lines[child_idx:], from_depth=child_depth
                        )
                else:
                    # we're at EOF
                    child_idx += 1
                    child_line = None

                # If this is a bracket or end statement, and the parent
                # is the same depth as the closing bracket/statement, then
                # we do want to include the line at child_idx, since it closes
                # the bracket/statement. This only works because LineSplitter
                # will always put a closing bracket at the start of a new line
                if (
                    child_depth == parent_depth
                    and child_line
                    and child_line.nodes[0].token.type
                    in (
                        TokenType.BRACKET_CLOSE,
                        TokenType.STATEMENT_END,
                    )
                ):
                    child_idx += 1

                # Now we merge the slice from parent_idx:child_idx
                try:
                    merged_line = self.create_merged_line(lines, parent_idx, child_idx)
                except CannotMergeException:
                    break

                if len(merged_line) <= self.mode.line_length:
                    lines[parent_idx:child_idx] = [merged_line]
                    # continuing to iterate over the same scanner won't work, since
                    # the indexes have changed. Recurse to merge the tail
                    lines[parent_idx + 1 :] = self.maybe_merge_lines(
                        lines[parent_idx + 1 :]
                    )
                    break

        return lines
