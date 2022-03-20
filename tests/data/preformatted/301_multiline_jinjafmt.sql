with
    base_spine as (
        {{
            dbt_utils.date_spine(
                datepart="day",
                start_date="'2021-01-01'::date",
                end_date="sysdate() + interval '1 year'",
            )
        }}
    ),
    final as (
        select
            date_day as dt,
            date_trunc('month', date_day) as mnth,
            date_part('day', date_day) as day_of_month
        from base_spine
    )

select *
from final
