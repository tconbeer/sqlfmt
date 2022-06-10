(
    select *
    from "data_warehouse"."order_status"
    where var1 is not null and var2 is not null
    limit 100
)
UNION
    (
        select *
        from "data_warehouse"."order_status"
        where var1 is not null and var2 is not null
        limit 100
    )
union
    select *
    from "data_warehouse"."order_status"
    where var1 is not null and var2 is not null
    limit 100

        union

        (
        select *
        from "data_warehouse"."order_status"
        where var1 is not null and var2 is not null
        limit 100
        )
)))))__SQLFMT_OUTPUT__(((((
(
    select *
    from "data_warehouse"."order_status"
    where var1 is not null and var2 is not null
    limit 100
)
union
(
    select *
    from "data_warehouse"."order_status"
    where var1 is not null and var2 is not null
    limit 100
)
union
select *
from "data_warehouse"."order_status"
where var1 is not null and var2 is not null
limit 100

union

(
    select *
    from "data_warehouse"."order_status"
    where var1 is not null and var2 is not null
    limit 100
)
