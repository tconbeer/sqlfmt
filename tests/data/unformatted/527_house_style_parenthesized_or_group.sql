select order_id, status
from orders
where (status = 'shipped' or status = 'delivered') and total > 100 and region = 'west'
)))))__SQLFMT_OUTPUT__(((((
select order_id, status

from orders

where (status = 'shipped' or status = 'delivered')
    and total > 100
    and region = 'west'
