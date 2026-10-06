SELECT customer_id, SUM(order_total) AS total
FROM orders
WHERE status = 'completed'
GROUP BY customer_id
HAVING SUM(order_total) > 100
ORDER BY total DESC
QUALIFY ROW_NUMBER() OVER (ORDER BY total DESC) = 1
LIMIT 10
)))))__SQLFMT_OUTPUT__(((((
select customer_id, sum(order_total) as total

from orders

where status = 'completed'

group by customer_id

having sum(order_total) > 100

order by total desc

qualify row_number() over (order by total desc) = 1

limit 10
