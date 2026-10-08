select
    case
        when status = 'a' and region = 'us' then 'x'
        when status = 'b' then 'y'
        else 'z'
    end as flag
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    case
        when status = 'a'
            and region = 'us'
            then 'x'
        when status = 'b' then 'y'
        else 'z'
    end as flag

from orders
