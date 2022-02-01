{% test nonnegative(model, column_name) %}
select *
from {{model}}
where {{ column_name }} < 0
{% endtest %}
)))))__SQLFMT_OUTPUT__(((((
{% test nonnegative(model, column_name) %}
select * from {{ model }} where {{ column_name }} < 0
{% endtest %}
