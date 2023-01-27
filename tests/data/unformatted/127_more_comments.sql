-- source: https://github.com/tconbeer/sqlfmt/issues/348
with table_a as (
    select
        /* Notice that this select statement can fit on a single line without comments */
        col1,
        col2, -- col2
        /* Special column */
        special_column,
    from {{ ref("table_a" )}}
)

/* Some interesting comments above a CTE with a leading comma */
, table_b as (
    select *
    from {{ ref("table_b") }}
)

select *
from table_a, table_b;

select 1
-- two
, 2 -- two inline
-- three
, 3 -- three inline
, 4 -- four inline
)))))__SQLFMT_OUTPUT__(((((
-- source: https://github.com/tconbeer/sqlfmt/issues/348
with
    table_a as (
        select
            /* Notice that this select statement can fit on a single line without comments */
            col1,
            col2,  -- col2
            /* Special column */
            special_column,
        from {{ ref("table_a") }}
    ),
    /* Some interesting comments above a CTE with a leading comma */
    table_b as (select * from {{ ref("table_b") }})

select *
from table_a, table_b
;

select
    1,
    -- two
    2,  -- two inline
    -- three
    3,  -- three inline
    4  -- four inline
