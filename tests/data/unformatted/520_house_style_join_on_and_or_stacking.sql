select o.id, a.street
from orders o
left join addresses a on a.id = o.address_id and a.active = true and a.country = 'US'
)))))__SQLFMT_OUTPUT__(((((
select
    o.id,
    a.street

from orders o

left join addresses a
    on a.id = o.address_id
    and a.active = true
    and a.country = 'US'
