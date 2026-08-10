-- see: https://github.com/tconbeer/sqlfmt/issues/553
-- a quote run that is not a triple-quoted string must not be lexed as one
select '''' || 'quoted_text' || ''''
select ''''''''
select """" || "quoted_text" || """"
select """"""""
select '''3229''' as test
select '''quoted_text''' as triple
select """quoted_text""" as triple_double
select '''it's here''' as apostrophe_inside
select '''''' as empty_triple
select """""" as empty_triple_double
select '''' as escaped_quote
select """" as escaped_double_quote
select '' as empty
select "" as empty_double
select $$'$$ || 'quoted_text' || $$'$$ as dollar_quoted
select """a'b""" as apostrophe_inside_triple_double
select r'''raw''' as raw_triple
select r"""raw""" as raw_triple_double
select b'''bytes''' as bytes_triple
select b"""bytes""" as bytes_triple_double
select '''a
b''' as multiline_triple
select """a
b""" as multiline_triple_double
