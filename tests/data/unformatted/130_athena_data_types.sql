-- source: https://github.com/tconbeer/sqlfmt/issues/500
select 
cast(
json_parse(foo) as array<
    map<varchar,varchar>>) 
from dwh.table
)))))__SQLFMT_OUTPUT__(((((
-- source: https://github.com/tconbeer/sqlfmt/issues/500
select cast(json_parse(foo) as array<map<varchar, varchar>>) from dwh.table
