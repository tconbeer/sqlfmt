from dataclasses import dataclass
from typing import List

from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode
from sqlfmt.token import Token, TokenType


@dataclass
class LineMerger:
    mode: Mode

    def maybe_merge_lines(self, lines: List[Line]) -> List[Line]:
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
            a,
            b,
            max(
                greatest(
                    a,
                    b
                )
            ) as c
        """
        MAX_LENGTH = self.mode.line_length

        # scan for suitable parents. Parents must have a change in depth > 0
        # before merging
        scanner = enumerate(lines)
        for idx, parent_line in scanner:
            if parent_line.change_in_depth > 0:
                parent_idx = idx
                parent_depth = parent_line.depth
                parent_token = parent_line.nodes[-2].token
                if parent_token.type == TokenType.TOP_KEYWORD:
                    parent_depth += 1
                child_depth = parent_depth
                child_idx = parent_idx
                while child_depth >= parent_depth:
                    try:
                        child_idx, child_line = next(scanner)
                    except StopIteration:
                        child_idx += 1
                        break
                    child_depth = child_line.depth
                    if child_line.change_in_depth > 0:
                        lines[child_idx:] = self.maybe_merge_lines(lines[child_idx:])
                source_string = parent_line.source_string
                merged_nodes: List[Node] = []
                for line in lines[parent_idx:child_idx]:
                    nodes = [
                        node
                        for node in line.nodes
                        if node.token.type != TokenType.NEWLINE
                    ]
                    merged_nodes.extend(nodes)
                merged_line = Line.from_nodes(
                    source_string=source_string,
                    previous_node=parent_line.previous_node,
                    nodes=merged_nodes,
                )
                nl = Token(
                    type=TokenType.NEWLINE,
                    prefix="",
                    token="\n",
                    spos=(
                        merged_nodes[-1].token.epos[0],
                        merged_nodes[-1].token.epos[1] + 1,
                    ),
                    epos=(
                        merged_nodes[-1].token.epos[0],
                        merged_nodes[-1].token.epos[1] + 2,
                    ),
                    line=merged_nodes[-1].token.line,
                )
                merged_line.append_token(nl)
                if len(merged_line) <= MAX_LENGTH:
                    lines[parent_idx:child_idx] = [merged_line]

        return lines
