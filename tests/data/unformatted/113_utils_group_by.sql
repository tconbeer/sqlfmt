select field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    count(*)
from my_table
where something_is_true
{{ dbt_utils.group_by(10) }} -- todo: keep line break
)))))__SQLFMT_OUTPUT__(((((
select
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    field_a,
    count(*)
from my_table
where something_is_true {{ dbt_utils.group_by(10) }}  -- todo: keep line break
