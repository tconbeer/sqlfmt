# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE: https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
{{ simple_cte([
      ('sfdc_user_hierarchy_live', 'prep_crm_user_hierarchy_live'),
      ('sfdc_user_hierarchy_stamped', 'prep_crm_user_hierarchy_stamped'),
      ('sales_qualified_source', 'prep_sales_qualified_source'),
      ('order_type', 'prep_order_type'),
      ('alliance_type', 'prep_alliance_type'),
      ('channel_type', 'prep_channel_type'),
      ('date_details_source', 'date_details_source')
])}}

, date AS (

   SELECT DISTINCT
     fiscal_month_name_fy,
     fiscal_year,
     first_day_of_month
   FROM date_details_source

), target_matrix AS (

    SELECT
      sheetload_sales_funnel_targets_matrix_source.*,
      date.first_day_of_month,
      date.fiscal_year,
      {{ get_keyed_nulls('sales_qualified_source.dim_sales_qualified_source_id') }}   AS dim_sales_qualified_source_id,
      {{ get_keyed_nulls('order_type.dim_order_type_id') }}                           AS dim_order_type_id
    FROM {{ ref('sheetload_sales_funnel_targets_matrix_source' )}}
    LEFT JOIN date
      ON {{ sales_funnel_text_slugify("sheetload_sales_funnel_targets_matrix_source.month") }} = {{ sales_funnel_text_slugify("date.fiscal_month_name_fy") }}
    LEFT JOIN sales_qualified_source
      ON {{ sales_funnel_text_slugify("sheetload_sales_funnel_targets_matrix_source.opportunity_source") }} = {{ sales_funnel_text_slugify("sales_qualified_source.sales_qualified_source_name") }}
    LEFT JOIN order_type
      ON {{ sales_funnel_text_slugify("sheetload_sales_funnel_targets_matrix_source.order_type") }} = {{ sales_funnel_text_slugify("order_type.order_type_name") }}

), fy22_user_hierarchy AS (
/* 
For FY22, targets in the sheetload file were set at the user_area grain, so we join to the stamped hierarchy on the user_area. We also want to find the last user_area in the fiscal year
because if there were multiple hierarchies for this user_area, the last one created is assumed to be the correct version. It is necessary to have a 1:1 relationship between area in the target
sheetload and user_area in the hierarchy so the targets do not fan out.
*/

    SELECT *
    FROM sfdc_user_hierarchy_stamped
    WHERE fiscal_year = 2022
      AND is_last_user_area_in_fiscal_year = 1

), fy23_and_beyond_user_hierarchy AS (
/* 
For FY23 and beyond, targets in the sheetload file were set at the user_segment_geo_region_area grain, so we join to the stamped hierarchy on the user_segment_geo_region_area.
*/

    SELECT *
    FROM sfdc_user_hierarchy_stamped
    WHERE fiscal_year > 2022
      AND is_last_user_hierarchy_in_fiscal_year = 1

), unioned_targets AS (

    SELECT
      target_matrix.kpi_name,
      target_matrix.first_day_of_month,
      target_matrix.dim_sales_qualified_source_id,
      target_matrix.opportunity_source,
      target_matrix.dim_order_type_id,
      target_matrix.order_type, 
      target_matrix.fiscal_year,
      target_matrix.allocated_target,
      fy22_user_hierarchy.crm_opp_owner_sales_segment_geo_region_area_stamped,
      fy22_user_hierarchy.dim_crm_user_hierarchy_stamped_id,
      fy22_user_hierarchy.dim_crm_opp_owner_sales_segment_stamped_id,
      fy22_user_hierarchy.crm_opp_owner_sales_segment_stamped,
      fy22_user_hierarchy.dim_crm_opp_owner_geo_stamped_id,
      fy22_user_hierarchy.crm_opp_owner_geo_stamped,
      fy22_user_hierarchy.dim_crm_opp_owner_region_stamped_id,
      fy22_user_hierarchy.crm_opp_owner_region_stamped,
      fy22_user_hierarchy.dim_crm_opp_owner_area_stamped_id,
      fy22_user_hierarchy.crm_opp_owner_area_stamped
    FROM target_matrix
    LEFT JOIN fy22_user_hierarchy
      ON {{ sales_funnel_text_slugify("target_matrix.area") }} = {{ sales_funnel_text_slugify("fy22_user_hierarchy.crm_opp_owner_area_stamped") }}
    WHERE target_matrix.fiscal_year = 2022 

    UNION ALL

    SELECT
      target_matrix.kpi_name,
      target_matrix.first_day_of_month,
      target_matrix.dim_sales_qualified_source_id,
      target_matrix.opportunity_source,
      target_matrix.dim_order_type_id,
      target_matrix.order_type, 
      target_matrix.fiscal_year,
      target_matrix.allocated_target,
      fy23_and_beyond_user_hierarchy.crm_opp_owner_sales_segment_geo_region_area_stamped,
      fy23_and_beyond_user_hierarchy.dim_crm_user_hierarchy_stamped_id,
      fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_sales_segment_stamped_id,
      fy23_and_beyond_user_hierarchy.crm_opp_owner_sales_segment_stamped,
      fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_geo_stamped_id,
      fy23_and_beyond_user_hierarchy.crm_opp_owner_geo_stamped,
      fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_region_stamped_id,
      fy23_and_beyond_user_hierarchy.crm_opp_owner_region_stamped,
      fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_area_stamped_id,
      fy23_and_beyond_user_hierarchy.crm_opp_owner_area_stamped
    FROM target_matrix
    LEFT JOIN fy23_and_beyond_user_hierarchy
      ON {{ sales_funnel_text_slugify("target_matrix.area") }} = {{ sales_funnel_text_slugify("fy23_and_beyond_user_hierarchy.crm_opp_owner_sales_segment_geo_region_area_stamped") }}
        AND target_matrix.fiscal_year = fy23_and_beyond_user_hierarchy.fiscal_year
    WHERE target_matrix.fiscal_year > 2022 

), final_targets AS (

     SELECT

     {{ dbt_utils.surrogate_key(['unioned_targets.crm_opp_owner_sales_segment_geo_region_area_stamped', 
                                 'unioned_targets.fiscal_year', 
                                 'unioned_targets.kpi_name', 
                                 'unioned_targets.first_day_of_month', 
                                 'unioned_targets.opportunity_source',
                                 'unioned_targets.order_type',
                                 ]) }}                           AS sales_funnel_target_id,
     unioned_targets.kpi_name,
     unioned_targets.first_day_of_month,
     unioned_targets.fiscal_year,
     unioned_targets.opportunity_source                                                                                             AS sales_qualified_source,
     unioned_targets.dim_sales_qualified_source_id,
     unioned_targets.order_type,
     unioned_targets.dim_order_type_id,
     unioned_targets.crm_opp_owner_sales_segment_geo_region_area_stamped                                                             AS crm_user_sales_segment_geo_region_area,
     COALESCE(sfdc_user_hierarchy_live.dim_crm_user_hierarchy_live_id, unioned_targets.dim_crm_user_hierarchy_stamped_id)           AS dim_crm_user_hierarchy_live_id,
     COALESCE(sfdc_user_hierarchy_live.dim_crm_user_sales_segment_id, unioned_targets.dim_crm_opp_owner_sales_segment_stamped_id)   AS dim_crm_user_sales_segment_id,
     COALESCE(sfdc_user_hierarchy_live.dim_crm_user_geo_id, unioned_targets.dim_crm_opp_owner_geo_stamped_id)                       AS dim_crm_user_geo_id,
     COALESCE(sfdc_user_hierarchy_live.dim_crm_user_region_id, unioned_targets.dim_crm_opp_owner_region_stamped_id)                 AS dim_crm_user_region_id,
     COALESCE(sfdc_user_hierarchy_live.dim_crm_user_area_id, unioned_targets.dim_crm_opp_owner_area_stamped_id)                     AS dim_crm_user_area_id,
     unioned_targets.dim_crm_user_hierarchy_stamped_id,
     unioned_targets.dim_crm_opp_owner_sales_segment_stamped_id,
     unioned_targets.dim_crm_opp_owner_geo_stamped_id,
     unioned_targets.dim_crm_opp_owner_region_stamped_id,
     unioned_targets.dim_crm_opp_owner_area_stamped_id,
     SUM(unioned_targets.allocated_target)                                                                                          AS allocated_target

    FROM unioned_targets
    LEFT JOIN sfdc_user_hierarchy_live
      ON unioned_targets.dim_crm_user_hierarchy_stamped_id = sfdc_user_hierarchy_live.dim_crm_user_hierarchy_live_id
    {{ dbt_utils.group_by(n=19) }}

)

{{ dbt_audit(
    cte_ref="final_targets",
    created_by="@mcooperDD",
    updated_by="@michellecooper",
    created_date="2020-12-18",
    updated_date="2022-03-07"
) }}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE:
# https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
{{
    simple_cte(
        [
            ("sfdc_user_hierarchy_live", "prep_crm_user_hierarchy_live"),
            ("sfdc_user_hierarchy_stamped", "prep_crm_user_hierarchy_stamped"),
            ("sales_qualified_source", "prep_sales_qualified_source"),
            ("order_type", "prep_order_type"),
            ("alliance_type", "prep_alliance_type"),
            ("channel_type", "prep_channel_type"),
            ("date_details_source", "date_details_source"),
        ]
    )
}},
date as (

    select distinct fiscal_month_name_fy, fiscal_year, first_day_of_month
    from date_details_source

),
target_matrix as (

    select
        sheetload_sales_funnel_targets_matrix_source.*,
        date.first_day_of_month,
        date.fiscal_year,
        {{ get_keyed_nulls("sales_qualified_source.dim_sales_qualified_source_id") }}
        as dim_sales_qualified_source_id,
        {{ get_keyed_nulls("order_type.dim_order_type_id") }} as dim_order_type_id
    from {{ ref("sheetload_sales_funnel_targets_matrix_source") }}
    left join
        date
        on
        {{
            sales_funnel_text_slugify(
                "sheetload_sales_funnel_targets_matrix_source.month"
            )
        }}
        = {{ sales_funnel_text_slugify("date.fiscal_month_name_fy") }}
    left join
        sales_qualified_source
        on
        {{
            sales_funnel_text_slugify(
                "sheetload_sales_funnel_targets_matrix_source.opportunity_source"
            )
        }}
        =
        {{
            sales_funnel_text_slugify(
                "sales_qualified_source.sales_qualified_source_name"
            )
        }}
    left join
        order_type
        on
        {{
            sales_funnel_text_slugify(
                "sheetload_sales_funnel_targets_matrix_source.order_type"
            )
        }}
        = {{ sales_funnel_text_slugify("order_type.order_type_name") }}

),
fy22_user_hierarchy as (
    /* 
For FY22, targets in the sheetload file were set at the user_area grain, so we join to the stamped hierarchy on the user_area. We also want to find the last user_area in the fiscal year
because if there were multiple hierarchies for this user_area, the last one created is assumed to be the correct version. It is necessary to have a 1:1 relationship between area in the target
sheetload and user_area in the hierarchy so the targets do not fan out.
*/
    select *
    from sfdc_user_hierarchy_stamped
    where fiscal_year = 2022 and is_last_user_area_in_fiscal_year = 1

),
fy23_and_beyond_user_hierarchy as (
    /* 
For FY23 and beyond, targets in the sheetload file were set at the user_segment_geo_region_area grain, so we join to the stamped hierarchy on the user_segment_geo_region_area.
*/
    select *
    from sfdc_user_hierarchy_stamped
    where fiscal_year > 2022 and is_last_user_hierarchy_in_fiscal_year = 1

),
unioned_targets as (

    select
        target_matrix.kpi_name,
        target_matrix.first_day_of_month,
        target_matrix.dim_sales_qualified_source_id,
        target_matrix.opportunity_source,
        target_matrix.dim_order_type_id,
        target_matrix.order_type,
        target_matrix.fiscal_year,
        target_matrix.allocated_target,
        fy22_user_hierarchy.crm_opp_owner_sales_segment_geo_region_area_stamped,
        fy22_user_hierarchy.dim_crm_user_hierarchy_stamped_id,
        fy22_user_hierarchy.dim_crm_opp_owner_sales_segment_stamped_id,
        fy22_user_hierarchy.crm_opp_owner_sales_segment_stamped,
        fy22_user_hierarchy.dim_crm_opp_owner_geo_stamped_id,
        fy22_user_hierarchy.crm_opp_owner_geo_stamped,
        fy22_user_hierarchy.dim_crm_opp_owner_region_stamped_id,
        fy22_user_hierarchy.crm_opp_owner_region_stamped,
        fy22_user_hierarchy.dim_crm_opp_owner_area_stamped_id,
        fy22_user_hierarchy.crm_opp_owner_area_stamped
    from target_matrix
    left join
        fy22_user_hierarchy
        on {{ sales_funnel_text_slugify("target_matrix.area") }}
        =
        {{ sales_funnel_text_slugify("fy22_user_hierarchy.crm_opp_owner_area_stamped") }}
    where target_matrix.fiscal_year = 2022

    union all

    select
        target_matrix.kpi_name,
        target_matrix.first_day_of_month,
        target_matrix.dim_sales_qualified_source_id,
        target_matrix.opportunity_source,
        target_matrix.dim_order_type_id,
        target_matrix.order_type,
        target_matrix.fiscal_year,
        target_matrix.allocated_target,
        fy23_and_beyond_user_hierarchy.crm_opp_owner_sales_segment_geo_region_area_stamped,
        fy23_and_beyond_user_hierarchy.dim_crm_user_hierarchy_stamped_id,
        fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_sales_segment_stamped_id,
        fy23_and_beyond_user_hierarchy.crm_opp_owner_sales_segment_stamped,
        fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_geo_stamped_id,
        fy23_and_beyond_user_hierarchy.crm_opp_owner_geo_stamped,
        fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_region_stamped_id,
        fy23_and_beyond_user_hierarchy.crm_opp_owner_region_stamped,
        fy23_and_beyond_user_hierarchy.dim_crm_opp_owner_area_stamped_id,
        fy23_and_beyond_user_hierarchy.crm_opp_owner_area_stamped
    from target_matrix
    left join
        fy23_and_beyond_user_hierarchy
        on {{ sales_funnel_text_slugify("target_matrix.area") }}
        =
        {{
            sales_funnel_text_slugify(
                "fy23_and_beyond_user_hierarchy.crm_opp_owner_sales_segment_geo_region_area_stamped"
            )
        }}
        and target_matrix.fiscal_year = fy23_and_beyond_user_hierarchy.fiscal_year
    where target_matrix.fiscal_year > 2022

),
final_targets as (

    select

        {{
            dbt_utils.surrogate_key(
                [
                    "unioned_targets.crm_opp_owner_sales_segment_geo_region_area_stamped",
                    "unioned_targets.fiscal_year",
                    "unioned_targets.kpi_name",
                    "unioned_targets.first_day_of_month",
                    "unioned_targets.opportunity_source",
                    "unioned_targets.order_type",
                ]
            )
        }}
        as sales_funnel_target_id,
        unioned_targets.kpi_name,
        unioned_targets.first_day_of_month,
        unioned_targets.fiscal_year,
        unioned_targets.opportunity_source as sales_qualified_source,
        unioned_targets.dim_sales_qualified_source_id,
        unioned_targets.order_type,
        unioned_targets.dim_order_type_id,
        unioned_targets.crm_opp_owner_sales_segment_geo_region_area_stamped
        as crm_user_sales_segment_geo_region_area,
        coalesce(
            sfdc_user_hierarchy_live.dim_crm_user_hierarchy_live_id,
            unioned_targets.dim_crm_user_hierarchy_stamped_id
        ) as dim_crm_user_hierarchy_live_id,
        coalesce(
            sfdc_user_hierarchy_live.dim_crm_user_sales_segment_id,
            unioned_targets.dim_crm_opp_owner_sales_segment_stamped_id
        ) as dim_crm_user_sales_segment_id,
        coalesce(
            sfdc_user_hierarchy_live.dim_crm_user_geo_id,
            unioned_targets.dim_crm_opp_owner_geo_stamped_id
        ) as dim_crm_user_geo_id,
        coalesce(
            sfdc_user_hierarchy_live.dim_crm_user_region_id,
            unioned_targets.dim_crm_opp_owner_region_stamped_id
        ) as dim_crm_user_region_id,
        coalesce(
            sfdc_user_hierarchy_live.dim_crm_user_area_id,
            unioned_targets.dim_crm_opp_owner_area_stamped_id
        ) as dim_crm_user_area_id,
        unioned_targets.dim_crm_user_hierarchy_stamped_id,
        unioned_targets.dim_crm_opp_owner_sales_segment_stamped_id,
        unioned_targets.dim_crm_opp_owner_geo_stamped_id,
        unioned_targets.dim_crm_opp_owner_region_stamped_id,
        unioned_targets.dim_crm_opp_owner_area_stamped_id,
        sum(unioned_targets.allocated_target) as allocated_target

    from unioned_targets
    left join
        sfdc_user_hierarchy_live
        on unioned_targets.dim_crm_user_hierarchy_stamped_id
        = sfdc_user_hierarchy_live.dim_crm_user_hierarchy_live_id
        {{ dbt_utils.group_by(n=19) }}

)

{{
    dbt_audit(
        cte_ref="final_targets",
        created_by="@mcooperDD",
        updated_by="@michellecooper",
        created_date="2020-12-18",
        updated_date="2022-03-07",
    )
}}
