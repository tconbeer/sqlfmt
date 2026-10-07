select o.order_id
from orders as o
where exists (
    select 1 from order_items as i where i.order_id = o.order_id and i.qty > 0
)
)))))__SQLFMT_OUTPUT__(((((
select o.order_id

from orders o

where exists (

    select 1

    from order_items i

    where i.order_id = o.order_id
        and i.qty > 0

)
