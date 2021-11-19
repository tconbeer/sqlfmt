# from copy import deepcopy
# from typing import List

# import pytest

# from sqlfmt.line import Line, Node, SqlfmtBracketError
# from sqlfmt.mode import Mode
# from sqlfmt.parser import Query
# from sqlfmt.token import Token, TokenType
# from tests.util import read_test_data


# @pytest.fixture
# def source_string() -> str:
#     return "with abc as (select * from my_table)\n"


# @pytest.fixture
# def bare_line(source_string: str) -> Line:
#     line = Line(source_string, previous_node=None)
#     return line


# @pytest.fixture
# def tokens(source_string: str) -> List[Token]:
#     tokens = [
#         Token(type=TokenType.UNTERM_KEYWORD, prefix="", token="with", spos=0, epos=4),
#         Token(type=TokenType.NAME, prefix=" ", token="abc", spos=4, epos=8),
#         Token(type=TokenType.WORD_OPERATOR, prefix=" ", token="as", spos=8, epos=11),
#         Token(type=TokenType.BRACKET_OPEN, prefix=" ", token="(", spos=11, epos=13),
#         Token(
#             type=TokenType.UNTERM_KEYWORD, prefix="", token="select", spos=13, epos=19
#         ),
#         Token(type=TokenType.STAR, prefix=" ", token="*", spos=19, epos=21),
#         Token(
#             type=TokenType.UNTERM_KEYWORD, prefix=" ", token="from", spos=21, epos=26
#         ),
#         Token(type=TokenType.NAME, prefix=" ", token="my_table", spos=26, epos=35),
#         Token(type=TokenType.BRACKET_CLOSE, prefix="", token=")", spos=35, epos=36),
#     ]
#     return tokens


# @pytest.fixture
# def simple_line(source_string: str, tokens: List[Token], bare_line: Line) -> Line:
#     simple_line = deepcopy(bare_line)
#     for token in tokens:
#         simple_line.append_token(token)
#     return simple_line


# def test_bare_line(source_string: str, bare_line: Line) -> None:
#     assert bare_line.source_string == source_string
#     assert str(bare_line) == ""

#     assert not bare_line.starts_with_unterm_keyword
#     assert not bare_line.contains_unterm_keyword
#     assert not bare_line.contains_multiline_node
#     assert not bare_line.ends_with_comment
#     assert not bare_line.is_standalone_comment
#     assert not bare_line.is_standalone_multiline_node
#     assert not bare_line.is_too_long(88)
#     assert not bare_line.can_be_depth_split


# def test_simple_line(
#     source_string: str, tokens: List[Token], simple_line: Line
# ) -> None:
#     assert simple_line.depth == 0
#     assert simple_line.change_in_depth == 1
#     assert len(simple_line.nodes) == len(tokens)
#     assert simple_line.open_brackets == [tokens[0]]
#     assert simple_line.depth_split == 1
#     assert simple_line.first_comma is None

#     assert str(simple_line) == source_string

#     expected_token_repr = (
#         "Token(type=TokenType.UNTERM_KEYWORD, prefix='', "
#         "token='with', spos=0, epos=4)"
#     )
#     assert repr(simple_line.tokens[0]) == expected_token_repr
#     new_token = eval(repr(simple_line.tokens[0]))
#     assert simple_line.tokens[0] == new_token

#     expected_node_repr = (
#         "Node(\n\ttoken='Token(type=TokenType.UNTERM_KEYWORD, token=with, "
#         "spos=0)',\n\tprevious_node=None,\n\tinherited_depth=0,\n\tdepth=0,"
#         "\n\tchange_in_depth=1,\n\tprefix=' ',\n\tvalue='with',\n\topen_brackets=["
#         "'Token(type=TokenType.UNTERM_KEYWORD, token=with, spos=0)']"
#         "\n\tformatting_disabled=False\n)"
#     )
#     assert repr(simple_line.nodes[0]) == expected_node_repr

#     assert simple_line.starts_with_unterm_keyword
#     assert simple_line.contains_unterm_keyword
#     assert not simple_line.contains_multiline_node
#     assert not simple_line.ends_with_comment
#     assert not simple_line.is_standalone_comment
#     assert not simple_line.is_standalone_multiline_node
#     assert not simple_line.is_too_long(88)
#     assert simple_line.can_be_depth_split


# def test_ends_with_comment(simple_line: Line) -> None:

#     last_node = simple_line.nodes[-1]
#     assert not last_node.token.type == TokenType.COMMENT
#     assert not simple_line.ends_with_comment

#     comment = Token(
#         type=TokenType.COMMENT,
#         prefix="",
#         token="-- my comment",
#         spos=last_node.token.epos,
#         epos=last_node.token.epos + 13,
#     )

#     simple_line.append_token(comment)

#     assert simple_line.nodes[-1].token.type == TokenType.COMMENT
#     assert simple_line.ends_with_comment

#     assert not simple_line.is_standalone_comment


# def test_is_standalone_comment(bare_line: Line, simple_line: Line) -> None:

#     assert not bare_line.is_standalone_comment
#     assert not simple_line.is_standalone_comment

#     comment = Token(
#         type=TokenType.COMMENT,
#         prefix="",
#         token="-- my comment",
#         spos=0,
#         epos=13,
#     )

#     bare_line.append_token(comment)
#     simple_line.append_token(comment)

#     assert bare_line.is_standalone_comment
#     assert not simple_line.is_standalone_comment


# def test_is_standalone_multiline_node(bare_line: Line, simple_line: Line) -> None:

#     assert not bare_line.is_standalone_multiline_node
#     assert not simple_line.is_standalone_multiline_node

#     comment = Token(
#         type=TokenType.COMMENT,
#         prefix="",
#         token="/*\nmy comment\n*/",
#         spos=0,
#         epos=18,
#     )

#     bare_line.append_token(comment)
#     simple_line.append_token(comment)

#     assert bare_line.is_standalone_comment
#     assert bare_line.is_standalone_multiline_node
#     assert not simple_line.is_standalone_comment
#     assert not simple_line.is_standalone_multiline_node


# def test_last_content_index(simple_line: Line) -> None:
#     idx = simple_line.last_content_index
#     assert str(simple_line.nodes[idx]) == ")"


# def test_calculate_depth_exception() -> None:

#     close_paren = Token(
#         type=TokenType.BRACKET_CLOSE,
#         prefix="",
#         token=")",
#         spos=0,
#         epos=1,
#     )

#     with pytest.raises(SqlfmtBracketError):
#         Node.calculate_depth(close_paren, inherited_depth=0, open_brackets=[])


# # this is failing because now we strip newlines from source
# @pytest.mark.xfail
# def test_closes_bracket_from_previous_line(
#     simple_line: Line, default_mode: Mode
# ) -> None:
#     assert not simple_line.closes_bracket_from_previous_line

#     source_string = (
#         "case\n"
#         "    when\n"
#         "        (\n"
#         "            field_one\n"
#         "            + (field_two)\n"
#         "            + field_three\n"
#         "        )\n"
#         "    then true\n"
#         "end\n"
#     )
#     q = Query.from_source(source_string=source_string, mode=default_mode)
#     result = [line.closes_bracket_from_previous_line for line in q.lines]
#     expected = [False, False, False, False, False, False, True, False, True]
#     assert result == expected


# def test_identifier_whitespace(default_mode: Mode) -> None:
#     """
#     Ensure we do not inject spaces into qualified identifier names
#     """
#     source_string = (
#         "my_schema.my_table,\n"
#         "my_schema.*,\n"
#         "{{ my_schema }}.my_table,\n"
#         "my_schema.{{ my_table }},\n"
#         "my_database.my_schema.my_table,\n"
#         'my_schema."my_table",\n'
#         '"my_schema".my_table,\n'
#         '"my_schema"."my_table",\n'
#         '"my_schema".*,\n'
#     )
#     q = Query.from_source(source_string=source_string, mode=default_mode)
#     parsed_string = "".join(str(line) for line in q.lines)
#     assert parsed_string == source_string.replace("\n", " ").rstrip() + "\n"


# def test_capitalization(default_mode: Mode) -> None:
#     source_string = (
#         'SELECT A, B, "C", {{ D }}, e, \'f\', \'G\'\nfROM "H"."j" Join I ON k And L\n'
#     )
#     expected = (
#         'select a, b, "C", {{ D }}, e, \'f\', \'G\' from "H"."j" join i on k and l\n'
#     )
#     q = Query.from_source(source_string=source_string, mode=default_mode)
#     parsed_string = "".join(str(line) for line in q.lines)
#     assert parsed_string == expected


# # this will fail until we can test it on split lines... q now only contains one line
# @pytest.mark.xfail
# def test_formatting_disabled(default_mode: Mode) -> None:
#     source_string, _ = read_test_data(
#         "unit_tests/test_line/test_formatting_disabled.sql"
#     )
#     q = Query.from_source(source_string=source_string, mode=default_mode)
#     expected = [
#         False,  # select
#         True,  # -- fmt: off
#         True,  # 1, 2, 3
#         True,  # 4, 5, 6
#         True,  # -- fmt: on
#         False,  # from something
#         True,  # join something_else -- fmt: off
#         True,  # --fmt: on
#         False,  # where format is true
#     ]
#     actual = [line.formatting_disabled for line in q.lines]
#     assert actual == expected
