# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if var('product_warehouse_event_sources') %}

with events as (select * from {{ ref('int_web_events') }}
/*  {% if is_incremental() %}
    where visitor_id in (
        select distinct visitor_id
        from {{ref('int_web_events')}}
        where cast(event_ts as datetime) >= (
          select
            {{ dbt_utils.dateadd(
                'hour',
                -var('web_sessionization_trailing_window'),
                'max(event_ts)'
            ) }}
          from {{ this }})
        )
    {% endif %}
*/
),

numbered as (

    select

        *,

        row_number() over (
            partition by visitor_id
            order by event_ts
          ) as event_number

    from events

),

lagged as (

    select

        *,

        lag(event_ts) over (
            partition by visitor_id
            order by event_number
          ) as previous_event_ts

    from numbered

),

diffed as (

    select
        *,
        {{ dbt_utils.datediff('event_ts','previous_event_ts','second') }} as period_of_inactivity

    from lagged

),

new_sessions as (


    select
        *,
        case
            when period_of_inactivity*-1 <= {{var('web_inactivity_cutoff')}} then 0
            else 1
        end as new_session
    from diffed

),

session_numbers as (


    select

        *,

        sum(new_session) over (
            partition by visitor_id
            order by event_number
            rows between unbounded preceding and current row
            ) as session_number

    from new_sessions

),

session_ids AS (

  SELECT
    event_id,
    event_type,
    event_ts,
    event_details,
    page_title,
    page_url_path,
    referrer_host,
    search,
    page_url,
    page_url_host,
    gclid,
    utm_term,
    utm_content,
    utm_medium,
    utm_campaign,
    utm_source,
    ip,
    visitor_id,
    user_id,
    device,
    device_category,
    event_number,
    md5(CAST( CONCAT(coalesce(CAST(visitor_id AS string ),
     ''), '-', coalesce(CAST(session_number AS string ),
     '')) AS string )) AS session_id,
    site,
    order_id,
    total_revenue,
    currency_code
  FROM
    session_numbers ),
id_stitching as (

    select * from {{ref('int_web_events_user_stitching')}}

),

joined as (

    select

        session_ids.*,

        coalesce(id_stitching.user_id, session_ids.visitor_id)
            as blended_user_id

    from session_ids
    left join id_stitching on id_stitching.visitor_id = session_ids.visitor_id

),
ordered as (
  select *,
         row_number() over (partition by blended_user_id order by event_ts) as event_seq,
         row_number() over (partition by blended_user_id, session_id order by event_ts) as event_in_session_seq
         ,

         case when event_type = 'Page View'
         and session_id = lead(session_id,1) over (partition by visitor_id order by event_number)
         then {{ dbt_utils.datediff('lead(event_ts,1) over (partition by visitor_id order by event_number)','event_ts','SECOND') }} end time_on_page_secs
  from joined

)
,
ordered_conversion_tagged as (
  SELECT o.*
{% if var('attribution_conversion_event_type') %}
  ,
       case when o.event_type in ('{{ var('attribution_conversion_event_type') }}','{{ var('attribution_create_account_event_type') }}') then lag(o.page_url,1) over (partition by o.blended_user_id order by o.event_seq) end as converting_page_url,
       case when o.event_type in ('{{ var('attribution_conversion_event_type') }}','{{ var('attribution_create_account_event_type') }}') then lag(o.page_title,1) over (partition by o.blended_user_id order by o.event_seq) end as converting_page_title,
       case when o.event_type in ('{{ var('attribution_conversion_event_type') }}','{{ var('attribution_create_account_event_type') }}') then lag(o.page_url,2) over (partition by o.blended_user_id order by o.event_seq) end as pre_converting_page_url,
       case when o.event_type in ('{{ var('attribution_conversion_event_type') }}','{{ var('attribution_create_account_event_type') }}') then lag(o.page_title,2) over (partition by o.blended_user_id order by o.event_seq) end as pre_converting_page_title,
{% endif %}
  FROM ordered o)
select *
from ordered_conversion_tagged


{% else %}

  {{config(enabled=false)}}

{% endif %}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if var("product_warehouse_event_sources") %}

with
    /*  {% if is_incremental() %}
    where visitor_id in (
        select distinct visitor_id
        from {{ref('int_web_events')}}
        where cast(event_ts as datetime) >= (
          select
            {{ dbt_utils.dateadd(
                'hour',
                -var('web_sessionization_trailing_window'),
                'max(event_ts)'
            ) }}
          from {{ this }})
        )
    {% endif %}
*/
    events as (select * from {{ ref("int_web_events") }}),

    numbered as (

        select

            *,

            row_number() over (
                partition by visitor_id order by event_ts
            ) as event_number

        from events

    ),

    lagged as (

        select

            *,

            lag(event_ts) over (
                partition by visitor_id order by event_number
            ) as previous_event_ts

        from numbered

    ),

    diffed as (

        select
            *,
            {{ dbt_utils.datediff("event_ts", "previous_event_ts", "second") }}
            as period_of_inactivity

        from lagged

    ),

    new_sessions as (
        select
            *,
            case
                when period_of_inactivity * -1 <= {{ var("web_inactivity_cutoff") }}
                then 0
                else 1
            end as new_session
        from diffed

    ),

    session_numbers as (
        select

            *,

            sum(new_session) over (
                partition by visitor_id
                order by event_number
                rows between unbounded preceding and current row
            ) as session_number

        from new_sessions

    ),

    session_ids as (

        select
            event_id,
            event_type,
            event_ts,
            event_details,
            page_title,
            page_url_path,
            referrer_host,
            search,
            page_url,
            page_url_host,
            gclid,
            utm_term,
            utm_content,
            utm_medium,
            utm_campaign,
            utm_source,
            ip,
            visitor_id,
            user_id,
            device,
            device_category,
            event_number,
            md5(
                cast(
                    concat(
                        coalesce(cast(visitor_id as string), ''),
                        '-',
                        coalesce(cast(session_number as string), '')
                    ) as string
                )
            ) as session_id,
            site,
            order_id,
            total_revenue,
            currency_code
        from session_numbers
    ),
    id_stitching as (select * from {{ ref("int_web_events_user_stitching") }}),

    joined as (

        select

            session_ids.*,

            coalesce(id_stitching.user_id, session_ids.visitor_id) as blended_user_id

        from session_ids
        left join id_stitching on id_stitching.visitor_id = session_ids.visitor_id

    ),
    ordered as (
        select
            *,
            row_number() over (
                partition by blended_user_id order by event_ts
            ) as event_seq,
            row_number() over (
                partition by blended_user_id, session_id order by event_ts
            ) as event_in_session_seq,

            case
                when
                    event_type = 'Page View'
                    and session_id = lead(session_id, 1) over (
                        partition by visitor_id order by event_number
                    )
                then
                    {{
                        dbt_utils.datediff(
                            "lead(event_ts,1) over (partition by visitor_id order by event_number)",
                            "event_ts",
                            "SECOND",
                        )
                    }}
            end time_on_page_secs
        from joined

    ),
    ordered_conversion_tagged as (
        select
            o.*
            {% if var("attribution_conversion_event_type") %}
            ,
            case
                when
                    o.event_type in (
                        '{{ var(' attribution_conversion_event_type ') }}',
                        '{{ var(' attribution_create_account_event_type ') }}'
                    )
                then
                    lag(o.page_url, 1) over (
                        partition by o.blended_user_id order by o.event_seq
                    )
            end as converting_page_url,
            case
                when
                    o.event_type in (
                        '{{ var(' attribution_conversion_event_type ') }}',
                        '{{ var(' attribution_create_account_event_type ') }}'
                    )
                then
                    lag(o.page_title, 1) over (
                        partition by o.blended_user_id order by o.event_seq
                    )
            end as converting_page_title,
            case
                when
                    o.event_type in (
                        '{{ var(' attribution_conversion_event_type ') }}',
                        '{{ var(' attribution_create_account_event_type ') }}'
                    )
                then
                    lag(o.page_url, 2) over (
                        partition by o.blended_user_id order by o.event_seq
                    )
            end as pre_converting_page_url,
            case
                when
                    o.event_type in (
                        '{{ var(' attribution_conversion_event_type ') }}',
                        '{{ var(' attribution_create_account_event_type ') }}'
                    )
                then
                    lag(o.page_title, 2) over (
                        partition by o.blended_user_id order by o.event_seq
                    )
            end as pre_converting_page_title,
            {% endif %}
        from ordered o
    )
select *
from ordered_conversion_tagged


{% else %} {{ config(enabled=false) }}

{% endif %}
