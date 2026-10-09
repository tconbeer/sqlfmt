select o.id, c.name
from orders o
inner join customers c on o.customer_id = c.id
)))))__SQLFMT_OUTPUT__(((((
select
    o.id,
    c.name

from orders o

inner join customers c
    on o.customer_id = c.id
