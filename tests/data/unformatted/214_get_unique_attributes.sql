{# Source: https://github.com/tconbeer/sqlfmt/issues/326 #}
{% macro get_unique_attributes(source_table, node_col) %}

{% set attribute_query %} 
    select
        distinct x.key as attributes
    from {{ source_table }} x
    where startswith(x.key, '@')  -- attributes get parsed as keys that start with '@'
        and length(x.key) > 1 -- but keys of just '@' designate the node itself
        and regexp_count(x.path, '\\[') > 1 -- we don't need the attributes from the xml root node
        and not startswith(x.key, '@xmlns') -- we don't need attributed data about xml namespaces
{% endset %}

{% set results = run_query(attribute_query) %}

{% if execute %}
    {% set results_list = results.columns[0].values() %}
{% else %}
    {% set results_list = [] %}
{% endif %}

{% for attribute in results_list %}
    , get({{ node_col }}, '{{ attribute }}')::varchar(256) as attribute_{{ dbt_utils.slugify(attribute) | replace("@", "") }}
{% endfor %}

{% endmacro %}
)))))__SQLFMT_OUTPUT__(((((
{# Source: https://github.com/tconbeer/sqlfmt/issues/326 #}
{% macro get_unique_attributes(source_table, node_col) %}

    {% set attribute_query %}
    select
        distinct x.key as attributes
    from {{ source_table }} x
    where startswith(x.key, '@')  -- attributes get parsed as keys that start with '@'
        and length(x.key) > 1 -- but keys of just '@' designate the node itself
        and regexp_count(x.path, '\\[') > 1 -- we don't need the attributes from the xml root node
        and not startswith(x.key, '@xmlns') -- we don't need attributed data about xml namespaces
    {% endset %}

    {% set results = run_query(attribute_query) %}

    {% if execute %} {% set results_list = results.columns[0].values() %}
    {% else %} {% set results_list = [] %}
    {% endif %}

    {% for attribute in results_list %}
        ,
        get({{ node_col }}, '{{ attribute }}')::varchar(
            256
        ) as attribute_{{ dbt_utils.slugify(attribute) | replace("@", "") }}
    {% endfor %}

{% endmacro %}
