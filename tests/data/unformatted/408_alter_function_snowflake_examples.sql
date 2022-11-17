-- COPYRIGHT SNOWFLAKE
-- https://docs.snowflake.com/en/sql-reference/sql/alter-function.html
alter function if exists function1(number) rename to function2;
alter function function2(number) set secure;
alter function function4(number) set api_integration = api_integration_2;
alter function function5(number) set max_batch_rows = 100;
)))))__SQLFMT_OUTPUT__(((((
-- COPYRIGHT SNOWFLAKE
-- https://docs.snowflake.com/en/sql-reference/sql/alter-function.html
alter function if exists function1(number)
rename to function2
;
alter function function2(number)
set secure
;
alter function function4(number)
set api_integration = api_integration_2
;
alter function function5(number)
set max_batch_rows = 100
;
