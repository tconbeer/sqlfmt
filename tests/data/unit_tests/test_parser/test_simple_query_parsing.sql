select
    a_long_field_name,
    another_long_field_name,
    (one_field + another_field) as c
from my_schema."my_QUOTED_ table!"
where one_field < another_field