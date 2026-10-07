select
    a_field, -- inline comment on a_field
    -- standalone comment before b_field
    b_field
from my_table -- trailing comment on from
where status = 'active' -- inline comment on where
)))))__SQLFMT_OUTPUT__(((((
select
    a_field,  -- inline comment on a_field
    -- standalone comment before b_field
    b_field

from my_table  -- trailing comment on from

where status = 'active'  -- inline comment on where
