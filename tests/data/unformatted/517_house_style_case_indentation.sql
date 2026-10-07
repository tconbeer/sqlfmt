select
    case
        when status = 'active' then 1
        else 0
    end as is_active,
    case
        when status = 'pending' then 'p'
        when status = 'done' then 'd'
        else 'u'
    end as status_code
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    case when status = 'active' then 1 else 0 end as is_active,
    case when status = 'pending' then 'p' when status = 'done' then 'd' else 'u' end as status_code

from orders
