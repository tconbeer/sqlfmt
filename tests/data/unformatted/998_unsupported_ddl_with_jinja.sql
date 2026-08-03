{% macro athena_unload_table(database, schema, table, unload_params) %}
    {% if execute %}
        UNLOAD (SELECT * FROM "{{ database }}".{{ schema }}."{{ table }}")
        TO '{{ s3_path }}'
        WITH (
          format = '{{ format }}'
          {% if compression %}, compression = '{{ compression }}' {% endif %}
        );
    {% endif %}
{% endmacro %}
)))))__SQLFMT_OUTPUT__(((((
{% macro athena_unload_table(database, schema, table, unload_params) %}
    {% if execute %}
        UNLOAD (SELECT * FROM "{{ database }}".{{ schema }}."{{ table }}")
        TO '{{ s3_path }}'
        WITH (
          format = '{{ format }}'
        {% if compression %}, compression = '{{ compression }}' {% endif %}
        );
    {% endif %}
{% endmacro %}
