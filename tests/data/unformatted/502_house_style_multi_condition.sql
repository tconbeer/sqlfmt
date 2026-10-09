select a, b
from my_table
where a = 1 and b = 2 and c = 3
group by a
having count(*) > 1 and sum(b) > 10
)))))__SQLFMT_OUTPUT__(((((
select
    a,
    b

from my_table

where a = 1
    and b = 2
    and c = 3

group by a

having count(*) > 1
    and sum(b) > 10
