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
),

-- stubbornly merge array indexes
func_that_returns_an_array(
    a_few_long_arguments,
    a_few_long_arguments,
    a_few_long_arguments,
)
[
    offset(
        1
    )
],

-- even when they don't fit on a line
func_that_returns_an_array(
    a_few_long_arguments,
    a_few_long_arguments,
    a_few_long_arguments,
)
[
    offset(
        func_that_returns_an_int(
            with_a_few_rather_verbose,
            arguments_that_need,
            some_space_and_cannot_be_merged,
            onto_a_single_line
        )
    )
]

-- stubbornly merge an operator that opens a paren (but only one)
fooooooooooooooooo 
+ barrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr(
    bazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
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
),

-- stubbornly merge array indexes
func_that_returns_an_array(
    a_few_long_arguments,
    a_few_long_arguments,
    a_few_long_arguments,
)[offset(1)],

-- even when they don't fit on a line
func_that_returns_an_array(
    a_few_long_arguments,
    a_few_long_arguments,
    a_few_long_arguments,
)[
    offset(
        func_that_returns_an_int(
            with_a_few_rather_verbose,
            arguments_that_need,
            some_space_and_cannot_be_merged,
            onto_a_single_line
        )
    )
]

-- stubbornly merge an operator that opens a paren (but only one)
fooooooooooooooooo + barrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr(
    bazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
)
