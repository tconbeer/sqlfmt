select
    customer_id,
    (
        select max(order_date) from orders where orders.customer_id = customers.customer_id
    ) as last_order_date
from customers
)))))__SQLFMT_OUTPUT__(((((
select
    customer_id,
    (
        select max(order_date)

        from orders

        where orders.customer_id = customers.customer_id

    ) as last_order_date

from customers
