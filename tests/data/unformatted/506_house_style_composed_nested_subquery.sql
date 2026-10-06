select s.customer_id, s.total
from (
    select customer_id, sum(order_total) as total
    from orders
    where status = 'completed'
    group by customer_id
    having sum(order_total) > 100
) as s
where s.total > 500
)))))__SQLFMT_OUTPUT__(((((
select s.customer_id, s.total

from
    (
        select customer_id, sum(order_total) as total

        from orders

        where status = 'completed'

        group by customer_id

        having sum(order_total) > 100
    ) s

where s.total > 500
