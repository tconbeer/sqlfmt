select
    coalesce(nullif(really_long_column_name_one_here, really_long_column_name_two_here), really_long_default_value_column_here, another_fallback_value_column_here) as result
from my_table
)))))__SQLFMT_OUTPUT__(((((
select
    coalesce(
        nullif(really_long_column_name_one_here, really_long_column_name_two_here),
        really_long_default_value_column_here,
        another_fallback_value_column_here
    ) as result

from my_table
