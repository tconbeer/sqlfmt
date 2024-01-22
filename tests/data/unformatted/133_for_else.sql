{% for i in range(5) %}
    select 1
{% else %}
    select 2
{% endfor %}
)))))__SQLFMT_OUTPUT__(((((
{% for i in range(5) %} select 1{% else %} select 2 {% endfor %}
