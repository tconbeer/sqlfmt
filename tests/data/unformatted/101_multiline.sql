{{
    config(
        materialized='table',
        sort='id',
        dist='all',
        post_hook='grant select on {{ this }} to role bi_role'
    )
}}

/*
 * This is a typical multiline comment.
 * It contains newlines.
 * And even /* some {% special characters %}
 * but we're not going to parse those
*/

with
    source as (select * from {{ ref('my_model') }}),
    renamed as ( /* This is a multiline comment in very bad style,
    * which starts and ends on lines with other tokens.
    */  select
            id,
            another_field,
            and_another,
            and_still_another
        from source
    ), {% set my_variable_in_bad_style = [
        "a",
        "short",
        "list",
        "of",
        "strings"
    ] %}

{#
 # And this is a nice multiline jinja comment
 # that we will also handle.
#}

select * from renamed /* what!?! */ where true
)))))__SQLFMT_OUTPUT__(((((
{{
    config(
        materialized='table',
        sort='id',
        dist='all',
        post_hook='grant select on {{ this }} to role bi_role'
    )
}}

/*
 * This is a typical multiline comment.
 * It contains newlines.
 * And even /* some {% special characters %}
 * but we're not going to parse those
*/
with
    source as (select * from {{ ref('my_model') }}),
    /* This is a multiline comment in very bad style,
    * which starts and ends on lines with other tokens.
    */
    renamed as (select id, another_field, and_another, and_still_another from source),
    {% set my_variable_in_bad_style = [
        "a",
        "short",
        "list",
        "of",
        "strings"
    ] %}

{#
 # And this is a nice multiline jinja comment
 # that we will also handle.
#}
/* what!?! */
select *
from renamed
where true
