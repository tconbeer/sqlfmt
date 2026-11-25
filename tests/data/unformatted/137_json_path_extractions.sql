-- https://github.com/tconbeer/sqlfmt/issues/269
select src:Salesperson.Name, parse_json(event_properties):numFieldsFilledIn from my_table
select my_array[I:J], my_table.MyColumn, src:tags[0].Name, src:Salesperson.Name:ManagerName from my_table
)))))__SQLFMT_OUTPUT__(((((
-- https://github.com/tconbeer/sqlfmt/issues/269
select src:Salesperson.Name, parse_json(event_properties):numFieldsFilledIn
from my_table
select
    my_array[i:j], my_table.mycolumn, src:tags[0].name, src:Salesperson.Name:ManagerName
from my_table
