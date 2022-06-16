select 
    *
from
    my_table
union all
select 
    *
from
    your_table
except
select 
    1,
    2,
    3

;
select 
    foo,
    bar,
    baz
from
    another_table