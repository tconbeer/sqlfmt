select
    case status
        when 'a' then 'active'
        when 'b' then 'blocked'
        else 'unknown'
    end as status_label,
    case grade
        when 'a' and bonus then 'top'
        else 'normal'
    end as grade_label
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    case status
        when 'a' then 'active'
        when 'b' then 'blocked'
        else 'unknown'
    end as status_label,
    case grade
        when 'a'
            and bonus
            then 'top'
        else 'normal'
    end as grade_label

from orders
