select order_id, customer_id
from orders
where customer_id in (
    select customer_id from customers where region = 'west' and active = true
)
)))))__SQLFMT_OUTPUT__(((((
select
    order_id,
    customer_id

from orders

where customer_id in (

    select customer_id

    from customers

    where region = 'west'
        and active = true

)
