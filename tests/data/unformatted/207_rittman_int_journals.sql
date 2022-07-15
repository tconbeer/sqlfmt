# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE: https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if var('finance_warehouse_journal_sources') %}


with journal_merge_list as
  (
    {% for source in var('finance_warehouse_journal_sources') %}

      {% set relation_source = 'stg_' + source + '_journals' %}

      select
        '{{source}}' as source,
        *
        from {{ ref(relation_source) }}

        {% if not loop.last %}union all{% endif %}
      {% endfor %}
  )
select * from journal_merge_list

{% else %}

{{config(enabled=false)}}

{% endif %}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT RITTMAN ANALYTICS
# LICENSED UNDER APACHE 2.0
# SEE:
# https://github.com/rittmananalytics/ra_data_warehouse/blob/d8dc7bd1c008ca79f9d09c909734e28a66ef6366/LICENSE.txt
{% if var("finance_warehouse_journal_sources") %}
with
    journal_merge_list as (
        {% for source in var("finance_warehouse_journal_sources") %}

        {% set relation_source = "stg_" + source + "_journals" %}

        select '{{source}}' as source, *
        from {{ ref(relation_source) }}

        {% if not loop.last %}
        union all
        {% endif %}
        {% endfor %}
    )
select *
from journal_merge_list

{% else %} {{ config(enabled=false) }}

{% endif %}
