/* a multiline
comment
*/
select
top
25
*
from "my table"
where
id not
in (
    1, 2, 3
)
union
all
select
distinct
*
from "your table"
)))))__SQLFMT_OUTPUT__(((((
/* a multiline
comment
*/
select top 25 *
from "my table"
where id not in (1, 2, 3)
union all
select distinct *
from "your table"
