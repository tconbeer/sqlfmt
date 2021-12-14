with
    one as (
        select --short
            1
    ),
    two as (
        select --too long to be one-lined with the comment inside so it'll have to go above
            a_long_enough_field,
            another_long_enough_field
    ),
    three as (
        select 1
    ), -- short enough
    four as (
        select --too long to be one-lined with the comment inside so it'll have to go above and be split and wrapped
            my_table.a_field,
            my_table.b_field,
            my_table.c_field
        from
            my_table
        where something == 5
    )

select -- not distinct
    one_really_long_field_name, -- with a long comment that needs to wrap above this line
    -- a standalone comment
    a_short_field, -- with another comment
    something_else,
    another_thing_entirely,
    yet_another_field
    -- another standalone comment
from a_really_long_table -- with a super long comment that won't fit here and needs to move up
)))))__SQLFMT_OUTPUT__(((((
with
    one as (select 1),  -- short
    -- too long to be one-lined with the comment inside so it'll have to go above
    two as (select a_long_enough_field, another_long_enough_field),
    three as (select 1),  -- short enough
    four as (
        -- too long to be one-lined with the comment inside so it'll have to go above
        -- and be split and wrapped
        select my_table.a_field, my_table.b_field, my_table.c_field
        from my_table
        where something == 5
    )
    
select  -- not distinct
    -- with a long comment that needs to wrap above this line
    one_really_long_field_name,
    -- a standalone comment
    -- with another comment
    a_short_field,
    something_else,
    another_thing_entirely,
    yet_another_field
-- another standalone comment
-- with a super long comment that won't fit here and needs to move up
from a_really_long_table
