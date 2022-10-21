delete from some_schema.some_table using another_schema.another_table
where some_table.id = another_table.id and some_table.delete_me is true returning *
)))))__SQLFMT_OUTPUT__(((((
delete from some_schema.some_table
using another_schema.another_table
where some_table.id = another_table.id and some_table.delete_me is true
returning *
