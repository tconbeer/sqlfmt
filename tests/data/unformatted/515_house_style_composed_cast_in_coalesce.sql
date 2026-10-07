select
    coalesce(cast(some_really_long_column_name_value as varchar), cast(another_long_default_value as varchar)) as result
from my_table
)))))__SQLFMT_OUTPUT__(((((
select
    coalesce(
        cast(some_really_long_column_name_value as varchar),
        cast(another_long_default_value as varchar)
    ) as result

from my_table
