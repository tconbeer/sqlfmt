create or replace warehouse foo
warehouse_size='XLARGE'
warehouse_type='SNOWPARK-OPTIMIZED'
max_cluster_count=6;
create
    warehouse if not exists foo
    with warehouse_size = 'X5LARGE'
        AUTO_SUSPEND = 100
        AUTO_RESUME = FALSE
        INITIALLY_SUSPENDED = TRUE;

alter warehouse if exists foo set warehouse_size='XSMALL'; alter warehouse if exists foo set tag 'foobar'='baz', 'another_really_long_tag_name'='really_very_long_tag_value_quxxxxxxxxxxxxxxxxxxx', 'bar'='baz';

alter warehouse foo rename to bar;
alter warehouse bar resume if suspended;
)))))__SQLFMT_OUTPUT__(((((
create or replace warehouse foo
warehouse_size = 'XLARGE'
warehouse_type = 'SNOWPARK-OPTIMIZED'
max_cluster_count = 6
;
create warehouse if not exists foo
with warehouse_size = 'X5LARGE'
auto_suspend = 100
auto_resume = false
initially_suspended = true
;

alter warehouse if exists foo
set warehouse_size = 'XSMALL'
;
alter warehouse if exists foo
set tag
    'foobar' = 'baz',
    'another_really_long_tag_name' = 'really_very_long_tag_value_quxxxxxxxxxxxxxxxxxxx',
    'bar' = 'baz'
;

alter warehouse foo
rename to bar
;
alter warehouse bar
resume if suspended
;
