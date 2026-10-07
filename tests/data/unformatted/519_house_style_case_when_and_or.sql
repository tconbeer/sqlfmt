select
    case
        when status = 'a' and region = 'us' then 'x'
        else 'y'
    end as flag_and,
    case
        when status = 'a' or status = 'b' then 'x'
        else 'y'
    end as flag_or,
    case
        when status = 'a' and region = 'us' and tier = 1 then 'x'
        else 'y'
    end as flag_multi
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    case
        when status = 'a'
            and region = 'us'
            then 'x'
        else 'y'
    end as flag_and,
    case
        when status = 'a'
            or status = 'b'
            then 'x'
        else 'y'
    end as flag_or,
    case
        when status = 'a'
            and region = 'us'
            and tier = 1
            then 'x'
        else 'y'
    end as flag_multi

from orders
