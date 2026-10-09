select s.customer_id, s.total
from (
    with filtered as (
        select * from orders where status = 'completed'
    )
    select customer_id, sum(amount) as total from filtered group by customer_id
) as s
where s.total > 500
)))))__SQLFMT_OUTPUT__(((((
select
    s.customer_id,
    s.total

from
    (

        with

        filtered as (

            select *

            from orders

            where status = 'completed'

        )

        select
            customer_id,
            sum(amount) as total

        from filtered

        group by customer_id

    ) s

where s.total > 500
