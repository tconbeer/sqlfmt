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
    union all (
            select
                'median_time_s' as ranking,
                client,
                category,
                canonicaldomain,
                median_time_s as metric,
                dense_rank() over (
                    partition by client order by median_time_s desc
                ) as sorted_order
            from base
        )
union all
with geos as (
SELECT *, 'mr' AS geo_code, 'Mauritania' AS geo, 'Africa' AS region, 'Western Africa' AS subregion FROM `chrome-ux-report.country_mr.201907` UNION ALL
SELECT *, 'mu' AS geo_code, 'Mauritius' AS geo, 'Africa' AS region, 'Eastern Africa' AS subregion FROM `chrome-ux-report.country_mu.201907` UNION ALL
SELECT *, 'yt' AS geo_code, 'Mayotte' AS geo, 'Africa' AS region, 'Eastern Africa' AS subregion FROM `chrome-ux-report.country_yt.201907`
) select geo from geos
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
union all
(
    select
        'median_time_s' as ranking,
        client,
        category,
        canonicaldomain,
        median_time_s as metric,
        dense_rank() over (
            partition by client order by median_time_s desc
        ) as sorted_order
    from base
)
union all
with
    geos as (
        select
            *,
            'mr' as geo_code,
            'Mauritania' as geo,
            'Africa' as region,
            'Western Africa' as subregion
        from `chrome-ux-report.country_mr.201907`
        union all
        select
            *,
            'mu' as geo_code,
            'Mauritius' as geo,
            'Africa' as region,
            'Eastern Africa' as subregion
        from `chrome-ux-report.country_mu.201907`
        union all
        select
            *,
            'yt' as geo_code,
            'Mayotte' as geo,
            'Africa' as region,
            'Eastern Africa' as subregion
        from `chrome-ux-report.country_yt.201907`
    )
select geo
from geos
