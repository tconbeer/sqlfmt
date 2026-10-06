{{ config(materialized='table', tags=['finance','daily']) }}

with
    stg_orders as (select * from raw.orders),
    stg_customers as (select * from raw.customers),
    joined as (
        select o.order_id, o.customer_id, c.name, o.order_total
        from stg_orders o
        inner join stg_customers c on o.customer_id = c.customer_id
        where o.order_total > 0
    )
select order_id, name, order_total from joined
)))))__SQLFMT_OUTPUT__(((((
{{ config(materialized="table", tags=["finance", "daily"]) }}

with
    stg_orders as (

        select * from raw.orders

    ),

    stg_customers as (

        select * from raw.customers

    ),

    joined as (

        select o.order_id, o.customer_id, c.name, o.order_total

        from stg_orders o
        inner join stg_customers c on o.customer_id = c.customer_id

        where o.order_total > 0

    )

select order_id, name, order_total

from joined
