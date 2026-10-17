-- DuckDB integer division operator
-- source: https://github.com/tconbeer/sqlfmt/issues/548
select 5 // 2;
select 10 // 3 as int_div;
select a // b from table1;
select 
    x // y as division,
    x / y as regular_division
from my_table
where z // 2 > 5;
-- regular comments should still work
select 1 -- this is a comment
;
select 2 # this is also a comment
;
select /* block comment */ 3;
)))))__SQLFMT_OUTPUT__(((((
-- DuckDB integer division operator
-- source: https://github.com/tconbeer/sqlfmt/issues/548
select 5 // 2
;
select 10 // 3 as int_div
;
select a // b
from table1
;
select x // y as division, x / y as regular_division
from my_table
where z // 2 > 5
;
-- regular comments should still work
select 1  -- this is a comment
;
select 2  # this is also a comment
;
select  /* block comment */
    3
;
