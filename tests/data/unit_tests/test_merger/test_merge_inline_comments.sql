with -- with
    tbl --tbl
    as ( -- as
        select -- select
            1 -- one
            ,
            2 -- two inline
            ,
            3 -- three inline
            ,
            4 -- four inline
    ) -- close
    ,
    second -- second
    as (
        select
            1
    )
    ,
    third
    as (
        select
            2
    ) -- third
select
    *
from
    tbl -- tbl
    ,
    second
    ,
    third
where
    a
    + b
    > fooooooooobarrrrrrrr -- this is a comment that is too long to be inline here. foobar
    and
    -- some other condition
    c
    + d
    < e

)))))__SQLFMT_OUTPUT__(((((
with  -- with
    tbl  -- tbl
    as (  -- as
        select  -- select
            1,  -- one
            2,  -- two inline
            3,  -- three inline
            4  -- four inline
    ),  -- close
    second  -- second
    as (select 1),
    third as (select 2)  -- third
select *
from
    tbl,  -- tbl
    second,
    third
where
    a + b > fooooooooobarrrrrrrr  -- this is a comment that is too long to be inline here. foobar
    -- some other condition
    and c + d < e
