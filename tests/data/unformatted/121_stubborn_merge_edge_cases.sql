-- COPYRIGHT RITTMAN ANALYTICS (with modifications)
-- LICENSED UNDER APACHE 2.0
-- SEE: https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
with
joined as (
        select
            d.*,
            d.days_in_deal_stage_0 + coalesce(d.days_in_deal_stage_1, 0) + coalesce(
                d.days_in_deal_stage_2,
                0
            ) + coalesce(d.days_in_deal_stage_3, 0) + coalesce(
                d.days_in_deal_stage_4,
                0
            ) + coalesce(d.days_in_deal_stage_5, 0) + coalesce(d.days_in_deal_stage_6, 0
            )
            + coalesce(d.days_in_deal_stage_7, 0) as days_in_pipeline,
            p.pipeline_label,
            p.pipeline_display_order,
            s.pipeline_stage_label,
            s.pipeline_stage_display_order,
            s.pipeline_stage_close_probability_pct,
            s.pipeline_stage_closed_won,
            u.owner_full_name,
            u.owner_email
        from renamed d
        join hubspot_deal_stages s on d.deal_pipeline_stage_id = s.pipeline_stage_id
        join hubspot_deal_pipelines_source p on s.pipeline_id = p.pipeline_id
        left outer join
            hubspot_deal_owners u on safe_cast(d.deal_owner_id as int64) = u.owner_id
    ),
    converting_sessions_deduped as (
        select
            session_id session_id,
            max(blended_user_id) as blended_user_id,
            sum(first_order_total_revenue) as first_order_total_revenue,
            sum(repeat_order_total_revenue) as repeat_order_total_revenue,
            max(currency_code) as currency_code,
            sum(count_first_order_conversions) as count_first_order_conversions,
            sum(count_repeat_order_conversions) as count_repeat_order_conversions,
            sum(count_order_conversions) as count_order_conversions,
            sum(count_registration_conversions) as count_registration_conversions,
            sum(count_registration_conversions) + sum(count_first_order_conversions)
            + sum(count_repeat_order_conversions) as count_conversions,
            max(converted_ts) as converted_ts
        from converting_events
        group by 1
    ),
select * from converting_sessions_deduped
)))))__SQLFMT_OUTPUT__(((((
-- COPYRIGHT RITTMAN ANALYTICS (with modifications)
-- LICENSED UNDER APACHE 2.0
-- SEE:
-- https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
with
    joined as (
        select
            d.*,
            d.days_in_deal_stage_0
            + coalesce(d.days_in_deal_stage_1, 0)
            + coalesce(d.days_in_deal_stage_2, 0)
            + coalesce(d.days_in_deal_stage_3, 0)
            + coalesce(d.days_in_deal_stage_4, 0)
            + coalesce(d.days_in_deal_stage_5, 0)
            + coalesce(d.days_in_deal_stage_6, 0)
            + coalesce(d.days_in_deal_stage_7, 0) as days_in_pipeline,
            p.pipeline_label,
            p.pipeline_display_order,
            s.pipeline_stage_label,
            s.pipeline_stage_display_order,
            s.pipeline_stage_close_probability_pct,
            s.pipeline_stage_closed_won,
            u.owner_full_name,
            u.owner_email
        from renamed d
        join hubspot_deal_stages s on d.deal_pipeline_stage_id = s.pipeline_stage_id
        join hubspot_deal_pipelines_source p on s.pipeline_id = p.pipeline_id
        left outer join
            hubspot_deal_owners u on safe_cast(d.deal_owner_id as int64) = u.owner_id
    ),
    converting_sessions_deduped as (
        select
            session_id session_id,
            max(blended_user_id) as blended_user_id,
            sum(first_order_total_revenue) as first_order_total_revenue,
            sum(repeat_order_total_revenue) as repeat_order_total_revenue,
            max(currency_code) as currency_code,
            sum(count_first_order_conversions) as count_first_order_conversions,
            sum(count_repeat_order_conversions) as count_repeat_order_conversions,
            sum(count_order_conversions) as count_order_conversions,
            sum(count_registration_conversions) as count_registration_conversions,
            sum(count_registration_conversions)
            + sum(count_first_order_conversions)
            + sum(count_repeat_order_conversions) as count_conversions,
            max(converted_ts) as converted_ts
        from converting_events
        group by 1
    ),
select *
from converting_sessions_deduped
