with
    one as (
        select --short
            1
    ),
    two as (
        select --too long but it's an inline comment so it has to stay here or we'll get stability issues
            a_long_enough_field,
            another_long_enough_field
    ),
    three as (
        select 1
    ), -- short enough
    four as (
        select
            my_table.a_field, --too long but it's an inline comment so it has to stay here or we'll get stability issues
            my_table.b_field,
            my_table.c_field
        from
            my_table
        where something == 5
    )

select -- not distinct
    one_really_long_field_name, -- with a long comment that will never wrap above this line
    -- a standalone comment
    a_short_field, -- with another comment
    something_else,
    another_thing_entirely,
    yet_another_field
    -- another standalone comment
from a_really_long_table; -- an inline comment on a semicolon

-- sometimes we like really long comments that wrap to many lines. And may even be a paragraph! This should wrap to a few lines (we can take that liberty because it's a standalone comment; we don't munge inline comments any more)
--
-- some people like blank lines between paragraphs of comments.
select 1
)))))__SQLFMT_OUTPUT__(((((
with
    one as (
        select  -- short
            1
    ),
    two as (
        select  -- too long but it's an inline comment so it has to stay here or we'll get stability issues
            a_long_enough_field, another_long_enough_field
    ),
    three as (select 1),  -- short enough
    four as (
        select
            my_table.a_field,  -- too long but it's an inline comment so it has to stay here or we'll get stability issues
            my_table.b_field,
            my_table.c_field
        from my_table
        where something == 5
    )

select  -- not distinct
    one_really_long_field_name,  -- with a long comment that will never wrap above this line
    -- a standalone comment
    a_short_field,  -- with another comment
    something_else,
    another_thing_entirely,
    yet_another_field
-- another standalone comment
from a_really_long_table  -- an inline comment on a semicolon
;

-- sometimes we like really long comments that wrap to many lines. And may even be a
-- paragraph! This should wrap to a few lines (we can take that liberty because it's a
-- standalone comment; we don't munge inline comments any more)
--
-- some people like blank lines between paragraphs of comments.
select 1
