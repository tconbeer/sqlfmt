-- COPYRIGHT SNOWFLAKE
-- SEE https://docs.snowflake.com/en/sql-reference/sql/create-function.html

create or replace function echo_varchar(x varchar)
returns varchar
language java
called on null input
handler='TestFunc.echoVarchar'
target_path='@~/testfunc.jar'
as
'class TestFunc {
  public static String echoVarchar(String x) {
    return x;
  }
}';

create function my_decrement_udf(i numeric(9, 0))
    returns numeric
    language java
    imports = ('@~/my_decrement_udf_package_dir/my_decrement_udf_jar.jar')
    handler = 'my_decrement_udf_package.my_decrement_udf_class.my_decrement_udf_method'
    ;

create or replace function js_factorial(d double)
  returns double
  language javascript
  strict
  as '
  if (D <= 0) {
    return 1;
  } else {
    var result = 1;
    for (var i = 2; i <= D; i++) {
      result = result * i;
    }
    return result;
  }
  ';

create or replace function py_udf()
  returns variant
  language python
  runtime_version = '3.8'
  packages = ('numpy','pandas','xgboost==1.5.0')
  handler = 'udf'
as $$
import numpy as np
import pandas as pd
import xgboost as xgb
def udf():
    return [np.__version__, pd.__version__, xgb.__version__]
$$;

create or replace function dream(i int)
  returns variant
  language python
  runtime_version = '3.8'
  handler = 'sleepy.snore'
  imports = ('@my_stage/sleepy.py')

create function pi_udf()
  returns float
  as '3.141592654::FLOAT'
  ;

create function simple_table_function ()
  returns table (x integer, y integer)
  as
  $$
    select 1, 2
    union all
    select 3, 4
  $$
  ;

create function multiply1 (a number, b number)
  returns number
  comment='multiply two numbers'
  as 'a * b';

create or replace function get_countries_for_user ( id number )
  returns table (country_code char, country_name varchar)
  as 'select distinct c.country_code, c.country_name
      from user_addresses a, countries c
      where a.user_id = id
      and c.country_code = a.country_code';
)))))__SQLFMT_OUTPUT__(((((
-- COPYRIGHT SNOWFLAKE
-- SEE https://docs.snowflake.com/en/sql-reference/sql/create-function.html
create or replace function echo_varchar(x varchar)
returns varchar
language java
called on null input
handler = 'TestFunc.echoVarchar'
target_path = '@~/testfunc.jar'
as 'class TestFunc {
  public static String echoVarchar(String x) {
    return x;
  }
}'
;

create function my_decrement_udf(i numeric(9, 0))
returns numeric
language java
imports = ('@~/my_decrement_udf_package_dir/my_decrement_udf_jar.jar')
handler = 'my_decrement_udf_package.my_decrement_udf_class.my_decrement_udf_method'
;

create or replace function js_factorial(d double)
returns double
language javascript
strict
as '
  if (D <= 0) {
    return 1;
  } else {
    var result = 1;
    for (var i = 2; i <= D; i++) {
      result = result * i;
    }
    return result;
  }
  '
;

create or replace function py_udf()
returns variant
language python runtime_version = '3.8'
packages = ('numpy', 'pandas', 'xgboost==1.5.0')
handler = 'udf'
as $$
import numpy as np
import pandas as pd
import xgboost as xgb
def udf():
    return [np.__version__, pd.__version__, xgb.__version__]
$$
;

create or replace function dream(i int)
returns variant
language python runtime_version = '3.8'
handler = 'sleepy.snore'
imports = ('@my_stage/sleepy.py')

create function pi_udf()
returns float
as '3.141592654::FLOAT'
;

create function simple_table_function()
returns table(x integer, y integer)
as $$
    select 1, 2
    union all
    select 3, 4
  $$
;

create function multiply1(a number, b number)
returns number
comment = 'multiply two numbers'
as 'a * b'
;

create or replace function get_countries_for_user(id number)
returns table(country_code char, country_name varchar)
as 'select distinct c.country_code, c.country_name
      from user_addresses a, countries c
      where a.user_id = id
      and c.country_code = a.country_code'
;
