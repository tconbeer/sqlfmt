select
    my_first_field,
    my_second_field as an_alias,
    case
        when another_field = 10
        then 12
    end as my_case_statement,
    case
        when my_field
        then 12
    end,
    another_field
from some_table