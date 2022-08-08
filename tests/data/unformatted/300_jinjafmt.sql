{{ config(materialized="incremental", unique_key="id", sort="timestamp", sort_type="compound", dist="user_id")}}

{% set model_name="jinjafmt"%}
{{ my_model_macro(
    name=model_name
)}}

{%set short_list = [
    'a',
    'b',
    'c'
]%}

{% set long_list = ["something_really_long", "something_else_long", "another_long_name", "and_another"] %}

{% do long_list.append(
    "another_long_name"
)%}

{{ dbt_utils.star(from=ref(model_name),
        except=long_list, relation_alias=model_name,
        suffix="something_else"
) }}

{{
    "something"
    ~ "something else"
    ~ "something else entirely"
}}

-- ensure jinja with python errors are not indented further when formatting
{% 
    extends layout_template 
    if layout_template is defined 
    else 'default.html' 
%}

with
    a as (

        select
            {{ dbt_utils.surrogate_key(var("surrogate_key_columns_menu_item_123456")) }}
            as order_item_id,
            -- this next line's jinja tag is one char too long
            {{ dbt_utils.surrogate_key(var("surrogate_key_columns_menu_item_1234567")) }}
            as menu_item_id,
        from b

    )

select *
from a

)))))__SQLFMT_OUTPUT__(((((
{{
    config(
        materialized="incremental",
        unique_key="id",
        sort="timestamp",
        sort_type="compound",
        dist="user_id",
    )
}}

{% set model_name = "jinjafmt" %}
{{ my_model_macro(name=model_name) }}

{% set short_list = ["a", "b", "c"] %}

{% set long_list = [
    "something_really_long",
    "something_else_long",
    "another_long_name",
    "and_another",
] %}

{% do long_list.append("another_long_name") %}

{{
    dbt_utils.star(
        from=ref(model_name),
        except=long_list,
        relation_alias=model_name,
        suffix="something_else",
    )
}}

{{ "something" ~ "something else" ~ "something else entirely" }}

-- ensure jinja with python errors are not indented further when formatting
{% 
    extends layout_template 
    if layout_template is defined 
    else 'default.html' 
%}

with
    a as (

        select
            {{ dbt_utils.surrogate_key(var("surrogate_key_columns_menu_item_123456")) }}
            as order_item_id,
            -- this next line's jinja tag is one char too long
            {{
                dbt_utils.surrogate_key(
                    var("surrogate_key_columns_menu_item_1234567")
                )
            }} as menu_item_id,
        from b

    )

select *
from a
