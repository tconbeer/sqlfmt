select o.order_id, recent.total
from orders as o
inner join (
    select customer_id, sum(amount) as total from payments group by customer_id
) as recent on recent.customer_id = o.customer_id
)))))__SQLFMT_OUTPUT__(((((
select
    o.order_id,
    recent.total

from orders o

inner join
    (

        select
            customer_id,
            sum(amount) as total

        from payments

        group by customer_id

    ) recent
    on recent.customer_id = o.customer_id
