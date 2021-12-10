select
    (
        my_table.something_super_interesting 
        * my_subquery.my_very_long_field_name
    )::decimal(
        10, 
        2
    ) / 100.00::decimal(
        10, 
        2
    ) as some_long_aliased_field_name
from
    my_table
    left join 
        (
            select 
                one_field, 
                two_fields, 
                sum(
                    something
                ), 
                my_very_long_field_name 
            from 
                another_table
        ) as mysubquery using(
            id
        )
)))))__SQLFMT_OUTPUT__(((((
select
    (
        my_table.something_super_interesting * my_subquery.my_very_long_field_name
    )::decimal(10, 2) / 100.00::decimal(10, 2) as some_long_aliased_field_name
from my_table
left join
    (
        select one_field, two_fields, sum(something), my_very_long_field_name
        from another_table
    ) as mysubquery using(id)
