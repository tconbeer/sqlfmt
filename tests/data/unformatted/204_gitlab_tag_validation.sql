# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE: https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
{% macro tag_validation() %}

    {%- if target.name != 'prod' -%}

        {% set data = namespace(all_tags=[]) %}

            {% for node in graph.nodes.values() %}

                {% set tags = node.tags %}

                {% set data.all_tags = data.all_tags + tags %}

            {% endfor %}
            
            {% for source in graph.sources.values() %}

                {% set tags = source.tags %}

                {% set data.all_tags = data.all_tags + tags %}

            {% endfor %}

        {% set project_tags = data.all_tags|unique|sort|list %}

        {% do log("Tags in Project: " ~ project_tags, info=true) %}

        {% set query %}
            SELECT tag
            FROM {{ref('valid_tags')}}
        {% endset %}
        
        {% set results = run_query(query) %}

        {% set valid_tags = results.columns[0].values()|sort|list %}

        {% do log("Tags in Validation File: " ~ valid_tags, info=true) %}

        {% set error_message = namespace(errors=[]) %}

        {% for tag in project_tags %}

            {% if tag not in valid_tags %}
                {% set error_message.errors = error_message.errors + ["Tag '" ~ tag ~ "' is present in the project but not in the tag_validation seed file."] %}
            {% endif %}

        {% endfor %}

        {% for tag in valid_tags %}

            {% if tag not in project_tags %}
                {% set error_message.errors = error_message.errors + ["Tag '" ~ tag ~ "' is present in the tag_validation seed file but not in project."] %}
            {% endif %}

        {% endfor %}

        {% if error_message.errors != [] %}
            
            {% for message in error_message.errors %}
                {% do log(message, info=true) %}
            {% endfor %}
            
            {% do exceptions.warn("Tag Validation Error") %}
        
        {% endif %}

    {% endif %}

{% endmacro %}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE:
# https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
{% macro tag_validation() %}

    {%- if target.name != "prod" -%}

        {% set data = namespace(all_tags=[]) %}

        {% for node in graph.nodes.values() %}

            {% set tags = node.tags %} {% set data.all_tags = data.all_tags + tags %}

        {% endfor %}

        {% for source in graph.sources.values() %}

            {% set tags = source.tags %} {% set data.all_tags = data.all_tags + tags %}

        {% endfor %}

        {% set project_tags = data.all_tags | unique | sort | list %}

        {% do log("Tags in Project: " ~ project_tags, info=true) %}

        {% set query %}
            SELECT tag
            FROM {{ref('valid_tags')}}
        {% endset %}

        {% set results = run_query(query) %}

        {% set valid_tags = results.columns[0].values() | sort | list %}

        {% do log("Tags in Validation File: " ~ valid_tags, info=true) %}

        {% set error_message = namespace(errors=[]) %}

        {% for tag in project_tags %}

            {% if tag not in valid_tags %}
                {% set error_message.errors = error_message.errors + [
                    "Tag '"
                    ~ tag
                    ~ "' is present in the project but not in the tag_validation seed file."
                ] %}
            {% endif %}

        {% endfor %}

        {% for tag in valid_tags %}

            {% if tag not in project_tags %}
                {% set error_message.errors = error_message.errors + [
                    "Tag '"
                    ~ tag
                    ~ "' is present in the tag_validation seed file but not in project."
                ] %}
            {% endif %}

        {% endfor %}

        {% if error_message.errors != [] %}

            {% for message in error_message.errors %}
                {% do log(message, info=true) %}
            {% endfor %}

            {% do exceptions.warn("Tag Validation Error") %}

        {% endif %}

    {% endif %}

{% endmacro %}
