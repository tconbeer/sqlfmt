# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE: https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if var("subscriptions_warehouse_sources")  %}


with plans_breakout_merge_list as
  (
    SELECT *
    FROM   {{ ref('stg_baremetrics_plan_breakout') }}
  )
select * from plans_breakout_merge_list

{% else %}

{{
    config(
        enabled=false
    )
}}


{% endif %}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE:
# https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if var("subscriptions_warehouse_sources") %}


with
    plans_breakout_merge_list as (
        select * from {{ ref("stg_baremetrics_plan_breakout") }}
    )
select *
from plans_breakout_merge_list

{% else %} {{ config(enabled=false) }}


{% endif %}
