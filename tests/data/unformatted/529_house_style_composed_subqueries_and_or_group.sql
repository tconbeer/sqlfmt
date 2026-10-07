select o.order_id, recent.total
from orders as o
inner join (
    select customer_id, sum(amount) as total from payments group by customer_id
) as recent on recent.customer_id = o.customer_id
where o.customer_id in (
    select customer_id from customers where region = 'west' and active = true
)
and (o.status = 'shipped' or o.status = 'delivered')
and exists (
    select 1 from order_items as i where i.order_id = o.order_id
)
)))))__SQLFMT_OUTPUT__(((((
select o.order_id, recent.total

from orders o
inner join
    (

        select customer_id, sum(amount) as total

        from payments

        group by customer_id

    ) recent
    on recent.customer_id = o.customer_id

where
    o.customer_id in (

        select customer_id

        from customers

        where region = 'west'
            and active = true

    )
    and (o.status = 'shipped' or o.status = 'delivered')
    and exists (

        select 1

        from order_items i

        where i.order_id = o.order_id

    )
