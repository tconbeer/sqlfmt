select o.id, o.order_total as total
from orders as o
join customers as c on o.customer_id = c.id
)))))__SQLFMT_OUTPUT__(((((
select o.id, o.order_total as total

from orders o
inner join customers c
    on o.customer_id = c.id
