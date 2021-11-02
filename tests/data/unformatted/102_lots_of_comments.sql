with
    one as (
        select --short
            1
    ),
    two as (
        select --too long to be one-lined with the comment inside
            2,
            3
    ),
    three as (
        select 1
    ) -- short enough

select -- not distinct
    one_really_long_field_name, -- with a long comment that needs to wrap above this line
    -- a standalone comment
    a_short_field -- with another comment
    -- another standalone comment
from a_really_long_table -- with a super long comment that won't here and needs to move up
)))))__SQLFMT_OUTPUT__(((((
with
    --short 
    one as (select 1),
    --too long to be one-lined with the comment inside
    two as (select 2, 3),
    three as (select 1) -- short enough

select -- not distinct
    -- with a long comment that needs to wrap above this line
    one_really_long_field_name, 
    -- a standalone comment
    a_short_field -- with another comment
-- another standalone comment
-- with a super long comment that won't here and needs to move up
from a_really_long_table