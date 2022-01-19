{%- set block_o_text -%}
Hello! I'm data, not code.
?? I can contain any )) characters I'd like.
{%- endset -%}

{%- set list_o_models = [
    "model_a",
    "model_b",
    "model_c",
] -%}

with
    {%- for model in list_o_models %}{{ model }} as (select * from {{ ref(model) }}),{% endfor -%}
    base as (select * from {% if "Hello" in block_o_text %}{{ ref("hello") }}{% else %}{{ ref("goodbye") }}{% endif %}),
    joined as (
        select
            {% for model in list_o_models %}
                {{ model }}.column_a as {{ model }}_field{%- if not loop.last -%},{%- endif %}{% endfor %}
        from 
            base
            {% for model in list_o_models %}join {{ model }} on base.{{ model }}_id = {{ model }}.id
            {% endfor %}
    )
select * from joined
)))))__SQLFMT_OUTPUT__(((((
{%- set block_o_text -%}
Hello! I'm data, not code.
?? I can contain any )) characters I'd like.
{%- endset -%}

{%- set list_o_models = [
    "model_a",
    "model_b",
    "model_c",
] -%}

with
    {%- for model in list_o_models %}
    {{ model }} as (select * from {{ ref(model) }}),
    {% endfor -%}
    base as (
        select *
        from
            {% if "Hello" in block_o_text %}{{ ref("hello") }}
            {% else %}{{ ref("goodbye") }}
            {% endif %}
    ),
    joined as (
        select
            {% for model in list_o_models %}
            {{ model }}.column_a as {{ model }}_field
            {%- if not loop.last -%},{%- endif %}
            {% endfor %}
        from
            base
        {% for model in list_o_models %}
        join {{ model }} on base.{{ model }}_id = {{ model }}.id
        {% endfor %}
    )
select *
from joined
