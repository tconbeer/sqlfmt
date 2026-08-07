-- see: https://github.com/tconbeer/sqlfmt/issues/553
-- a quote run that is not a triple-quoted string must not be lexed as one
select '''' || 'quoted_text' || ''''
select ''''''''
select '''3229''' as test
select '''quoted_text''' as triple
select '''it's here''' as apostrophe_inside
select '''''' as empty_triple
select '''' as escaped_quote
select '' as empty
select $$'$$ || 'quoted_text' || $$'$$ as dollar_quoted
select """a'b""" as triple_double
select r'''raw''' as raw_triple
select b'''bytes''' as bytes_triple
select '''a
b''' as multiline_triple
