alter table project_id.dataset.my_table
set options (
    -- sample comment
    description = 'This is a table with a description'
);

create or replace table project_id.dataset.my_table as
select
    -- sample comment
    col1, col2, col3,
from my_dataset.my_table
;

create or replace table project_id.dataset.my_table as
select
    /* 
    sample
    multiline
    comment
    */
    col1, col2, col3,
from my_dataset.my_table
;
