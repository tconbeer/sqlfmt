with
    stg_orders as (select * from raw.orders),
    final as (
        select order_id from stg_orders where status = 'completed'
    )
select * from final
)))))__SQLFMT_OUTPUT__(((((
with

stg_orders as (

    select * from raw.orders

),

final as (

    select order_id

    from stg_orders

    where status = 'completed'

)

select * from final
