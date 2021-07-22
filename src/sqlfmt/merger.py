from dataclasses import dataclass
from typing import List, Optional

from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode
from sqlfmt.token import TokenType


@dataclass
class LineMerger:
    mode: Mode

    def maybe_merge_lines(self, lines: List[Line], from_depth: int = 0) -> List[Line]:
        """
        Mutates lines by combining lines if possible.

        We only merge lines when all of the following conditions are met:

        1. The merged line has the same depth as the following line
        2. The merged line is short enough

        Every time the next line indents, there is an opportunity to
        merge, by scanning the lines until the current depth
        is reached again. We do this recursively, by calling this
        method again, with a copied slice of lines

        select
            first_field,
            nullif(
                split_part(
                    full_name,
                    ' ',
                    2
                ),
                ''
            ) as last_name,
            another_field,
            yet_another_field,
            and_still_another_field
        from
            my_table
        where
            some_condition is true
        """
        MAX_LENGTH = self.mode.line_length
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

                # scan ahead until we get back to this depth, or hit EOF
                # note that we're using the same generator as parent loop
                child_line: Optional[Line]
                for child_idx, child_line in scanner:
                    child_depth = child_line.depth
                    if child_depth <= parent_depth:
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

                # if child is dedented past parent, we can't do any merging.
                # break to return lines as-is
                if child_depth < parent_depth:
                    break

                # child_idx has the same depth as the parent. If this is an
                # unterminated keyword, we don't want to include the line
                # at child_idx in the merged string. But if it's a bracket or
                # statement, we do want to include the line, since it closes
                # the bracket/statement. This only works because LineSplitter
                # will always put a closing bracket at the start of a new line
                if child_line and child_line.nodes[0].token.type in (
                    TokenType.BRACKET_CLOSE,
                    TokenType.STATEMENT_END,
                ):
                    child_idx += 1

                # if the child is just one below the parent, we're trying to
                # merge a single line. break to return.
                if parent_idx - child_idx == 1:
                    break

                # we've scanned through all the children. Now we need to try to
                # merge.
                source_string = parent_line.source_string
                merged_nodes: List[Node] = []
                for line in lines[parent_idx:child_idx]:
                    # skip over nodes containing NEWLINEs
                    nodes = [
                        node
                        for node in line.nodes
                        if node.token.type != TokenType.NEWLINE
                    ]
                    merged_nodes.extend(nodes)
                if not merged_nodes:
                    # we only have whitespace/newlines
                    break
                merged_line = Line.from_nodes(
                    source_string=source_string,
                    previous_node=parent_line.previous_node,
                    nodes=merged_nodes,
                )
                merged_line.append_newline()
                if len(merged_line) <= MAX_LENGTH:
                    lines[parent_idx:child_idx] = [merged_line]
                    # continuing to iterate over the same scanner won't work, since
                    # the indexes have changed. Recurse to merge the tail
                    lines[parent_idx + 1 :] = self.maybe_merge_lines(
                        lines[parent_idx + 1 :]
                    )
                    break

        return lines
