from dataclasses import dataclass
from typing import Tuple

from black import re

from sqlfmt.exception import SqlfmtParsingError
from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode


@dataclass
class JinjaFormatter:
    mode: Mode

    def _format_python_string(self, source_string: str, max_length: int) -> str:
        if self.mode.no_jinjafmt:
            return source_string
        else:
            try:
                import black
                from black.parsing import InvalidInput
            except ImportError:
                return source_string
            else:
                black_mode = black.Mode(line_length=max_length)
                try:
                    formatted_string: str = black.format_str(
                        source_string, mode=black_mode
                    ).rstrip()
                except InvalidInput:
                    # the string isn't valid python.
                    # Jinja allows linebreaks where python doesn't
                    # so let's try again without newlines in the code
                    try:
                        flat_code = source_string.replace("\n", " ")
                        formatted_string = black.format_str(
                            flat_code, mode=black_mode
                        ).rstrip()
                    except InvalidInput:
                        # there is other jinja syntax that isn't valid python,
                        # so if this still fails, just stop trying
                        return source_string
                    else:
                        return formatted_string
                else:
                    return formatted_string

    def _split_jinja_tag_contents(self, tag: str) -> Tuple[str, str, str, str]:
        """
        Takes a jinja statement or expression and returns a tuple of its parts:
        (starting_marker, verb, code, ending_marker).

        "verb" is one of set, do, (TBD: if, elif, and for)

        For example, "{%- set my_var=4 %}" is split into
        ("{%-", "set", "my_var=4", "%}")
        """
        opening_marker_len = 3 if tag[2] == "-" else 2
        opening_marker = tag[:opening_marker_len]
        closing_marker_len = 3 if tag[-3] == "-" else 2
        closing_marker = tag[-closing_marker_len:]

        verb_pattern = r"\s*(set|do|for|if|elif|else|test|macro)\s+"
        verb_program = re.compile(verb_pattern, re.DOTALL | re.IGNORECASE)
        verb_match = verb_program.match(tag[opening_marker_len:])
        if verb_match:
            verb_pos = opening_marker_len + verb_match.span(1)[0]
            verb_epos = opening_marker_len + verb_match.span(1)[1]
            verb = tag[verb_pos:verb_epos]
        else:
            verb = ""
        verb_len = verb_match.span(0)[1] - verb_match.span(0)[0] if verb_match else 0

        code_pos = opening_marker_len + verb_len
        code = tag[code_pos:-closing_marker_len].strip()

        return opening_marker, verb, code, closing_marker

    def format_jinja_node(self, node: Node, max_length: int) -> None:
        """
        Format a single jinja tag. No-ops for nodes that
        are not jinja
        """
        if node.is_jinja:
            opening_marker, verb, code, closing_marker = self._split_jinja_tag_contents(
                node.value
            )
            if verb and code:
                verb = f"{verb} "
            if code:
                max_code_length = (
                    max_length
                    - len(opening_marker)
                    - len(verb)
                    - len(closing_marker)
                    - 2
                )
                try:
                    code = self._format_python_string(code, max_length=max_code_length)
                except SqlfmtParsingError as e:
                    raise SqlfmtParsingError(
                        "Could not parse jinja tag contents at position "
                        f"{node.token.spos}: {e}"
                    ) from e
            if "\n" in code and not verb:
                indent = " " * (4 * node.depth[0])
                node_lines = [f"{opening_marker}"]
                for code_line in code.splitlines(keepends=False):
                    node_lines.append(f"{indent}    {code_line}")
                node_lines.append(f"{indent}{closing_marker}")
                node.value = "\n".join(node_lines)
            else:
                node.value = f"{opening_marker} {verb.lower()}{code} {closing_marker}"

    def format_line(self, line: Line) -> None:
        """
        Format each jinja tag in a line, in turn
        """
        line_length = self.mode.line_length
        if line.contains_jinja:
            running_length = len(line.prefix) - len(line.nodes[0].prefix)
            for node in line.nodes:
                self.format_jinja_node(node, max_length=line_length - running_length)
                running_length += len(node)
