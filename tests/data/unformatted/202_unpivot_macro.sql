-- from https://github.com/dbt-labs/dbt-utils/blob/33299334a305d0acb99ebee8cc2eb6eb2ba5ca31/macros/sql/unpivot.sql
{% macro default__unpivot(relation=none, cast_to='varchar', exclude=none, remove=none, field_name='field_name', value_name='value', table=none) -%}

  {%- set exclude = exclude if exclude is not none else [] %}
  {%- set remove = remove if remove is not none else [] %}

  {%- set include_cols = [] %}

  {%- set table_columns = {} %}

  {%- do table_columns.update({relation: []}) %}

  {%- do dbt_utils._is_relation(relation, 'unpivot') -%}
  {%- do dbt_utils._is_ephemeral(relation, 'unpivot') -%}
  {%- set cols = adapter.get_columns_in_relation(relation) %}

  {%- for col in cols -%}
    {%- if col.column.lower() not in remove|map('lower') and col.column.lower() not in exclude|map('lower') -%}
      {% do include_cols.append(col) %}
    {%- endif %}
  {%- endfor %}


  {%- for col in include_cols -%}
    select
      {%- for exclude_col in exclude %}
        {{ exclude_col }},
      {%- endfor %}

      cast('{{ col.column }}' as {{ dbt_utils.type_string() }}) as {{ field_name }},
      cast(  {% if col.data_type == 'boolean' %}
           {{ dbt_utils.cast_bool_to_text(col.column) }}
             {% else %}
           {{ col.column }}
             {% endif %}
           as {{ cast_to }}) as {{ value_name }}

    from {{ relation }}

    {% if not loop.last -%}
      union all
    {% endif -%}
  {%- endfor -%}

{%- endmacro %}
)))))__SQLFMT_OUTPUT__(((((
-- from
-- https://github.com/dbt-labs/dbt-utils/blob/33299334a305d0acb99ebee8cc2eb6eb2ba5ca31/macros/sql/unpivot.sql
{% macro default__unpivot(
    relation=none,
    cast_to="varchar",
    exclude=none,
    remove=none,
    field_name="field_name",
    value_name="value",
    table=none
) -%}

{%- set exclude = exclude if exclude is not none else [] %}
{%- set remove = remove if remove is not none else [] %}

{%- set include_cols = [] %}

{%- set table_columns = {} %}

{%- do table_columns.update({relation: []}) %}

{%- do dbt_utils._is_relation(relation, "unpivot") -%}
{%- do dbt_utils._is_ephemeral(relation, "unpivot") -%}
{%- set cols = adapter.get_columns_in_relation(relation) %}

{%- for col in cols -%}
{%- if col.column.lower() not in remove | map(
    "lower"
) and col.column.lower() not in exclude | map("lower") -%}
{% do include_cols.append(col) %}
{%- endif %}
{%- endfor %}


{%- for col in include_cols -%}
select
    {%- for exclude_col in exclude %} {{ exclude_col }}, {%- endfor %}

    cast('{{ col.column }}' as {{ dbt_utils.type_string() }}) as {{ field_name }},
    cast(
        {% if col.data_type == "boolean" %}{{ dbt_utils.cast_bool_to_text(col.column) }}
        {% else %}{{ col.column }}
        {% endif %} as {{ cast_to }}
    ) as {{ value_name }}

from {{ relation }}

{% if not loop.last -%}
union all
{% endif -%}
{%- endfor -%}

{%- endmacro %}
