# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE: https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if target.type == 'bigquery' %}
{% if var("marketing_warehouse_deal_sources") %}
{% if 'hubspot_crm' in var("marketing_warehouse_deal_sources") %}
{% if var("stg_hubspot_crm_etl") == 'fivetran' %}


with source as (
  select *
  from {{ source('fivetran_hubspot_crm','deals') }}
),
hubspot_deal_company as (
  select *
  from {{ source('fivetran_hubspot_crm','deal_companies') }}
),
hubspot_deal_pipelines_source as (
  select *
  from  {{ source('fivetran_hubspot_crm','pipelines') }}
)
,
hubspot_deal_property_history as (
  select *
  from  {{ source('fivetran_hubspot_crm','property_history') }}
)
,
hubspot_deal_stages as (
  select *
  from  {{ source('fivetran_hubspot_crm','pipeline_stages') }}
),
hubspot_deal_owners as (
  SELECT *
  FROM {{ source('fivetran_hubspot_crm','owners') }}
),
renamed as (
  SELECT
      deal_id as deal_id,
      property_dealname     as deal_name,
      property_dealtype     as deal_type,
      property_description  as deal_description,
      deal_pipeline_stage_id as deal_pipeline_stage_id,
      deal_pipeline_id        as deal_pipeline_id,
      is_deleted             as deal_is_deleted,
      property_amount        as deal_amount,
      owner_id as deal_owner_id,
      property_amount_in_home_currency    as deal_amount_local_currency,
      property_closed_lost_reason         as deal_closed_lost_reason,
      property_closedate                  as deal_closed_date,
      property_createdate                 as deal_created_date,
      property_hs_lastmodifieddate        as deal_last_modified_date
      FROM
  source
),
joined as (
    select
    d.deal_id,
    concat('{{ var('stg_hubspot_crm_id-prefix') }}',cast(a.company_id as string)) as company_id,
    d.* except (deal_id),
    timestamp_millis(safe_cast(h.value as int64)) as deal_pipeline_stage_ts,
    p.label as pipeline_label,
    p.display_order as pipeline_display_order,
    s.label as pipeline_stage_label,
    s.display_order as pipeline_stage_display_order,
    s.probability as pipeline_stage_close_probability_pct,
    s.closed_won as pipeline_stage_closed_won,
    concat(u.first_name,' ',u.last_name) as owner_full_name,
    u.email as owner_email
  from
    renamed d
  left outer join
    hubspot_deal_company a
  on
    d.deal_id = a.deal_id
  left outer join
    hubspot_deal_property_history h
  on
    d.deal_id = h.deal_id and h.name = concat('hs_date_entered_',d.deal_pipeline_stage_id)
  join
    hubspot_deal_stages s
  on
    d.deal_pipeline_stage_id = s.stage_id
  join
    hubspot_deal_pipelines_source p
  on
    s.pipeline_id = p.pipeline_id
  left outer join
    hubspot_deal_owners u
  on
    safe_cast(d.deal_owner_id as int64) = u.owner_id
)
select * from joined

{% else %} {{config(enabled=false)}} {% endif %}
{% else %} {{config(enabled=false)}} {% endif %}
{% else %} {{config(enabled=false)}} {% endif %}
{% else %} {{config(enabled=false)}} {% endif %}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE:
# https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if target.type == "bigquery" %}
{% if var("marketing_warehouse_deal_sources") %}
{% if "hubspot_crm" in var("marketing_warehouse_deal_sources") %}
{% if var("stg_hubspot_crm_etl") == "fivetran" %}
with
    source as (select * from {{ source("fivetran_hubspot_crm", "deals") }}),
    hubspot_deal_company as (
        select * from {{ source("fivetran_hubspot_crm", "deal_companies") }}
    ),
    hubspot_deal_pipelines_source as (
        select * from {{ source("fivetran_hubspot_crm", "pipelines") }}
    ),
    hubspot_deal_property_history as (
        select * from {{ source("fivetran_hubspot_crm", "property_history") }}
    ),
    hubspot_deal_stages as (
        select * from {{ source("fivetran_hubspot_crm", "pipeline_stages") }}
    ),
    hubspot_deal_owners as (
        select * from {{ source("fivetran_hubspot_crm", "owners") }}
    ),
    renamed as (
        select
            deal_id as deal_id,
            property_dealname as deal_name,
            property_dealtype as deal_type,
            property_description as deal_description,
            deal_pipeline_stage_id as deal_pipeline_stage_id,
            deal_pipeline_id as deal_pipeline_id,
            is_deleted as deal_is_deleted,
            property_amount as deal_amount,
            owner_id as deal_owner_id,
            property_amount_in_home_currency as deal_amount_local_currency,
            property_closed_lost_reason as deal_closed_lost_reason,
            property_closedate as deal_closed_date,
            property_createdate as deal_created_date,
            property_hs_lastmodifieddate as deal_last_modified_date
        from source
    ),
    joined as (
        select
            d.deal_id,
            concat(
                '{{ var(' stg_hubspot_crm_id - prefix ') }}',
                cast(a.company_id as string)
            ) as company_id,
            d.* except (deal_id),
            timestamp_millis(safe_cast(h.value as int64)) as deal_pipeline_stage_ts,
            p.label as pipeline_label,
            p.display_order as pipeline_display_order,
            s.label as pipeline_stage_label,
            s.display_order as pipeline_stage_display_order,
            s.probability as pipeline_stage_close_probability_pct,
            s.closed_won as pipeline_stage_closed_won,
            concat(u.first_name, ' ', u.last_name) as owner_full_name,
            u.email as owner_email
        from renamed d
        left outer join hubspot_deal_company a on d.deal_id = a.deal_id
        left outer join
            hubspot_deal_property_history h
            on d.deal_id = h.deal_id
            and h.name = concat('hs_date_entered_', d.deal_pipeline_stage_id)
        join hubspot_deal_stages s on d.deal_pipeline_stage_id = s.stage_id
        join hubspot_deal_pipelines_source p on s.pipeline_id = p.pipeline_id
        left outer join
            hubspot_deal_owners u on safe_cast(d.deal_owner_id as int64) = u.owner_id
    )
select *
from joined

{% else %} {{ config(enabled=false) }}
{% endif %}
{% else %} {{ config(enabled=false) }}
{% endif %}
{% else %} {{ config(enabled=false) }}
{% endif %}
{% else %} {{ config(enabled=false) }}
{% endif %}
