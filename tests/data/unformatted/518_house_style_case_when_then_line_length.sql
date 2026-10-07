select
    case
        when a then b
    end as short_case,
    case
        when another_field = some_other_value then some_really_long_value
    end as still_fits,
    case
        when yet_another_condition_name then a_truly_excessively_long_result_value_that_pushes_this_line_well_past_the_hundred_character_limit_for_sure
    end as drops_then
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    case when a then b end as short_case,
    case when another_field = some_other_value then some_really_long_value end as still_fits,
    case
        when yet_another_condition_name
            then
                a_truly_excessively_long_result_value_that_pushes_this_line_well_past_the_hundred_character_limit_for_sure
    end as drops_then

from orders
