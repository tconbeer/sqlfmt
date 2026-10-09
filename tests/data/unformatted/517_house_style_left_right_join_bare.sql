select o.id, a.street, b.account_number
from orders o
left outer join addresses a on a.id = o.address_id
right outer join billing b on b.order_id = o.id
)))))__SQLFMT_OUTPUT__(((((
select
    o.id,
    a.street,
    b.account_number

from orders o

left join addresses a
    on a.id = o.address_id

right join billing b
    on b.order_id = o.id
