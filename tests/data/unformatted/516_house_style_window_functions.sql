SELECT
    a,
    SUM(a) OVER () AS running_total,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) AS rn,
    RANK() OVER (PARTITION BY customer_id ORDER BY order_date DESC) AS rk,
    COALESCE(SUM(a) OVER (PARTITION BY customer_id), 0) AS wrapped_total
FROM orders
)))))__SQLFMT_OUTPUT__(((((
select
    a,
    sum(a) over () as running_total,

    row_number() over (
        partition by customer_id
        order by order_date
    ) as rn,

    rank() over (
        partition by customer_id
        order by order_date desc
    ) as rk,

    coalesce(

        sum(a) over (
            partition by customer_id
        ),
        0

    ) as wrapped_total

from orders
