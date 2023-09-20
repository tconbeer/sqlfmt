-- source: https://github.com/tconbeer/sqlfmt/issues/468
select * from  {{ ref("events") }} e
// join from events table
left join {{ ref("users") }} u
on u.id = e.user_id
;
select "https://sqlfmt.com" as url_not_a_comment
from foo
)))))__SQLFMT_OUTPUT__(((((
-- source: https://github.com/tconbeer/sqlfmt/issues/468
select *
from {{ ref("events") }} e
-- join from events table
left join {{ ref("users") }} u on u.id = e.user_id
;
select "https://sqlfmt.com" as url_not_a_comment
from foo
