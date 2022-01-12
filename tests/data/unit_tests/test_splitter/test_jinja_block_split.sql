{{ config(materialized="table") }}

{%- set n = 5 -%}
with
    {% for i in range(n) %}
        dont_do_this_{{ i }} as (
            {% if foo %}select
            {% elif bar %}select distinct
            {% elif baz %}select top 25
            {% else %}select{% endif %}
                my_col
            from {% if i == qux %}zip{% else %}zap{% endif %}
        ){% if not loop.last %},{% endif%}
    {% endfor %}
{% for i in range(n) %}
    select * from dont_do_this_{{ i }}
    {% if not loop.last -%}union all{%- endif %}
{% endfor %}
)))))__SQLFMT_OUTPUT__(((((
{{ config(materialized="table") }}
{%- set n = 5 -%}
with
{% for i in range(n) %}
dont_do_this_{{ i }}
as (
{% if foo %}
select
{% elif bar %}
select distinct
{% elif baz %}
select top 25
{% else %}
select
{% endif %}
my_col
from
{% if i == qux %}
zip
{% else %}
zap
{% endif %}
)
{% if not loop.last %}
,
{% endif%}
{% endfor %}
{% for i in range(n) %}
select
*
from
dont_do_this_{{ i }}
{% if not loop.last -%}
union all
{%- endif %}
{% endfor %}
