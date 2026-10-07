select
    case
        when outer_status = 'a' then
            case
                when inner_flag and other_flag then 1
                else 2
            end
        else 3
    end as nested_result
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    case
        when outer_status = 'a'
            then
                case
                    when inner_flag
                        and other_flag
                        then 1
                    else 2
                end
        else 3
    end as nested_result

from orders
