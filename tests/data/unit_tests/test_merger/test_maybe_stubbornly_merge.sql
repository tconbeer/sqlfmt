-- try to merge the first line of this segment with the previous segment
count(
    *
) 
over (
    partition by
        foofoofoofoofoofoofoofoofoo
    order by
        foofoofoofoofoofoofoofoofoo asc
    rows between unbounded preceding and unbounded following
),

-- try to add this segment to the last line of the previous segment
(
    foofoofoofoofoofoofoofoofoo
    + barbarbarbarbarbarbarbarbar
    + bazbazbazbazbazbazbazbazbaz
)
::decimal(
    18,
    2
),

-- try to add just the first line of this segment to the last
-- line of the previous segment
sum(
    case
        when
            foo
        then
            foo + bar + baz
        when
            bar
        then
            bar + baz + qux
        when
            baz
        then
            something_else_long
    end
)
over (
    partition by
        foofoofoofoofoofoofoofoofoo
    order by
        foofoofoofoofoofoofoofoofoo asc
    rows between unbounded preceding and unbounded following
),

-- give up and just return the original segments
a_very_very_long_cte_name_that_is_just_under_eighty_eight_characters_in_length_xxxxxxx
as (
    select
        1
)
)))))__SQLFMT_OUTPUT__(((((
-- try to merge the first line of this segment with the previous segment
count(*) over (
    partition by
        foofoofoofoofoofoofoofoofoo
    order by
        foofoofoofoofoofoofoofoofoo asc
    rows between unbounded preceding and unbounded following
),

-- try to add this segment to the last line of the previous segment
(
    foofoofoofoofoofoofoofoofoo
    + barbarbarbarbarbarbarbarbar
    + bazbazbazbazbazbazbazbazbaz
)::decimal(18, 2),

-- try to add just the first line of this segment to the last
-- line of the previous segment
sum(
    case
        when
            foo
        then
            foo + bar + baz
        when
            bar
        then
            bar + baz + qux
        when
            baz
        then
            something_else_long
    end
) over (
    partition by
        foofoofoofoofoofoofoofoofoo
    order by
        foofoofoofoofoofoofoofoofoo asc
    rows between unbounded preceding and unbounded following
),

-- give up and just return the original segments
a_very_very_long_cte_name_that_is_just_under_eighty_eight_characters_in_length_xxxxxxx
as (
    select
        1
)
