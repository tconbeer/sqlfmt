select
    sum(case when status = 'a' then amount else 0 end) as total_a,
    sum(
        case
            when status = 'a' and region = 'us' then amount
            else 0
        end
    ) as total_a_us,
    coalesce(
        sum(
            case
                when status = 'a' then
                    case
                        when region = 'us' then amount
                        else amount * 2
                    end
                else 0
            end
        ),
        0
    ) as nested_case_in_sum
from orders
)))))__SQLFMT_OUTPUT__(((((
select
    sum(case when status = 'a' then amount else 0 end) as total_a,
    sum(

        case
            when status = 'a'
                and region = 'us'
                then amount
            else 0
        end

    ) as total_a_us,
    coalesce(
        sum(

            case
                when status = 'a'
                    then case when region = 'us' then amount else amount * 2 end
                else 0
            end

        ),
        0
    ) as nested_case_in_sum

from orders
