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
select
    *
from
    tbl -- tbl
    ,
    second
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
    as (select 1)
select *
from
    tbl,  -- tbl
    second
