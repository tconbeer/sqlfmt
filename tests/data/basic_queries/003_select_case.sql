select
    my_first_field,
    my_second_field as an_alias,
    case
        when another_field = some_other_value
        then some_really_long_value
    end as my_case_statement,
    case
        when caser
            then some_really_really_long_value_to_wrap_this_next_line
        else
            42
    end,
    CASE
        when (my_field) then end_field
    END::numeric(10, 2) as casted_case,
    (case when ending then false end)+(case when 2 then true end)::varchar(10),
    another_field,
    case when true then 10 end+4
from some_table
)))))__SQLFMT_OUTPUT__(((((
select
    my_first_field,
    my_second_field as an_alias,
    case
        when another_field = some_other_value
        then some_really_long_value
    end as my_case_statement,
    case
        when caser
        then some_really_really_long_value_to_wrap_this_next_line
        else 42
    end,
    case when (my_field) then end_field end::numeric(10, 2) as casted_case,
    (case when ending then false end) + (case when 2 then true end)::varchar(10),
    another_field,
    case when true then 10 end + 4
from some_table
