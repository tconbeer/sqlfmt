with
    source_table
    as (
        select
            *
        from
            {{ source('my_long_source_name', 'my_source_table') }}
    ),
    renamed
    as (
        select
            1
        from
            source_table
    )
select
    *
from
    renamed
window
    site_window
    as (
        partition by
            site_id
        order by
            observed_date asc
        rows between unbounded preceding and unbounded following
    )
)))))__SQLFMT_OUTPUT__(((((
with
    source_table as (
        select * from {{ source('my_long_source_name', 'my_source_table') }}
    ),
    renamed as (select 1 from source_table)
select *
from renamed
window
    site_window as (
        partition by site_id
        order by observed_date asc
        rows between unbounded preceding and unbounded following
    )
