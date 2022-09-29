SELECT * FROM test TABLESAMPLE (50 PERCENT);
SELECT * FROM a_super_duper_really_very_long_long_long_long_table_name TABLESAMPLE (BUCKET 4 OUT OF 10);
)))))__SQLFMT_OUTPUT__(((((
select *
from test tablesample(50 percent)
;
select *
from
    a_super_duper_really_very_long_long_long_long_table_name 
    tablesample (bucket 4 out of 10)
;
