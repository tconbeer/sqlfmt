import re
from dataclasses import dataclass, field
from importlib import import_module
from types import ModuleType
from typing import Optional

from sqlfmt.line import Line, Node
from sqlfmt.mode import Mode


class BlackWrapper:
    def __init__(self) -> None:
        try:
            self.black: Optional[ModuleType] = import_module("black")
        except ImportError:
            self.black = None

    def format_string(self, source_string: str, max_length: int) -> str:
        """
        Attempt to use black to format source_string to a line_length of max_length.
        Return source_string if black isn't installed or it can't parse source_string
        """
        formatted_string = source_string

        if not self.black:
            return formatted_string

        black_mode = self.black.Mode(line_length=max_length)  # type: ignore
        try:
            formatted_string = self.black.format_str(  # type: ignore
                source_string, mode=black_mode
            ).rstrip()
        except ValueError:
            # the string isn't valid python.
            # Jinja allows linebreaks where python doesn't
            # so let's try again without newlines in the code
            try:
                flat_code = source_string.replace("\n", " ")
                formatted_string = self.black.format_str(  # type: ignore
                    flat_code, mode=black_mode
                ).rstrip()
            except ValueError:
                # there is other jinja syntax that isn't valid python,
                # so if this still fails, just stop trying
                pass
        finally:
            return formatted_string


@dataclass
class JinjaTag:
    opening_marker: str
    verb: str
    code: str
    closing_marker: str
    depth: int

    def __str__(self) -> str:
        if self.is_indented_multiline_tag:
            return self._multiline_str()
        else:
            s = f"{self.opening_marker} {self.verb}{self.code} {self.closing_marker}"
            return s

    @property
    def is_indented_multiline_tag(self) -> bool:
        return self.code != "" and self.verb == "" and "\n" in self.code

    def _multiline_str(self) -> str:
        """
        if the formatted code is on multiple lines, and does not use a verb,
        we want the code indented four spaces past the opening and
        closing markers. The opening marker will already be indented to the
        proper depth
        """
        indent = " " * (4 * self.depth)
        lines = [f"{self.opening_marker}"]
        for code_line in self.code.splitlines(keepends=False):
            lines.append(f"{indent}    {code_line}")
        lines.append(f"{indent}{self.closing_marker}")
        return "\n".join(lines)

    @classmethod
    def from_string(cls, source_string: str, depth: int) -> "JinjaTag":
        """
        Takes a jinja statement or expression and returns a tuple of its parts:
        (starting_marker, verb, code, ending_marker).

        "verb" is one of set, do, (TBD: if, elif, and for)

        For example, "{%- set my_var=4 %}" is split into
        ("{%-", "set", "my_var=4", "%}")
        """
        opening_marker_len = 3 if source_string[2] == "-" else 2
        opening_marker = source_string[:opening_marker_len]
        closing_marker_len = 3 if source_string[-3] == "-" else 2
        closing_marker = source_string[-closing_marker_len:]

        verb_pattern = r"\s*(set|do|for|if|elif|else|test|macro)\s+"
        verb_program = re.compile(verb_pattern, re.DOTALL | re.IGNORECASE)
        verb_match = verb_program.match(source_string[opening_marker_len:])
        if verb_match:
            verb_pos = opening_marker_len + verb_match.span(1)[0]
            verb_epos = opening_marker_len + verb_match.span(1)[1]
            verb = source_string[verb_pos:verb_epos].lower()
        else:
            verb = ""
        verb_len = verb_match.span(0)[1] - verb_match.span(0)[0] if verb_match else 0

        code_pos = opening_marker_len + verb_len
        code = source_string[code_pos:-closing_marker_len].strip()

        if verb and code:
            verb = f"{verb} "

        return JinjaTag(opening_marker, verb, code, closing_marker, depth)

    def max_code_length(self, max_length: int) -> int:
        """
        For a tag with max_length remaining characters on the line, return the
        max length that the code inside the curlies (exc. the verb) can occupy.
        """
        return (
            max_length
            - len(self.opening_marker)
            - len(self.verb)
            - len(self.closing_marker)
            - 2
        )


@dataclass
class JinjaFormatter:
    mode: Mode
    code_formatter: BlackWrapper = field(default_factory=lambda: BlackWrapper())

    def format_line(self, line: Line) -> None:
        """
        Format each jinja tag in a line, in turn
        """
        line_length = self.mode.line_length
        if line.contains_jinja:
            running_length = len(line.prefix) - len(line.nodes[0].prefix)
            for node in line.nodes:
                self._format_jinja_node(node, max_length=line_length - running_length)
                running_length += len(node)

    def _format_jinja_node(self, node: Node, max_length: int) -> None:
        """
        Format a single jinja tag. No-ops for nodes that
        are not jinja
        """
        if node.is_jinja:
            tag = JinjaTag.from_string(node.value, node.depth[0])

            if tag.code:
                tag.code = self._format_python_string(
                    tag.code,
                    max_length=tag.max_code_length(max_length),
                )

            node.value = str(tag)

    def _format_python_string(self, source_string: str, max_length: int) -> str:
        if self.mode.no_jinjafmt:
            return source_string
        else:
            return self.code_formatter.format_string(source_string, max_length)
