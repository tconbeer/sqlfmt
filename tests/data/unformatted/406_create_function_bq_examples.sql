-- COPYRIGHT GOOGLE
-- SEE https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_function_statement

CREATE FUNCTION mydataset.multiply_Inputs(x FLOAT64, y FLOAT64)
RETURNS FLOAT64
AS (x * y);

CREATE TEMP FUNCTION multiplyInputs(x FLOAT64, y FLOAT64)
RETURNS FLOAT64
LANGUAGE js
AS r"""
  return x*y;
""";

SELECT multiplyInputs(a, b) FROM (SELECT 3 as a, 2 as b);

CREATE FUNCTION mydataset.remote_Multiply_Inputs(x FLOAT64, y FLOAT64)
RETURNS FLOAT64
REMOTE WITH CONNECTION us.myconnection
OPTIONS(endpoint="https://us-central1-myproject.cloudfunctions.net/multiply");

CREATE OR REPLACE TABLE FUNCTION mydataset.names_by_year(y INT64)
AS
  SELECT year, name, SUM(number) AS total
  FROM `bigquery-public-data.usa_names.usa_1910_current`
  WHERE year = y
  GROUP BY year, name;

CREATE OR REPLACE TABLE FUNCTION mydataset.names_by_year(y INT64)
RETURNS TABLE<name STRING, year INT64, total INT64>
AS
  SELECT year, name, SUM(number) AS total
  FROM `bigquery-public-data.usa_names.usa_1910_current`
  WHERE year = y
  GROUP BY year, name;
)))))__SQLFMT_OUTPUT__(((((
-- COPYRIGHT GOOGLE
-- SEE
-- https://cloud.google.com/bigquery/docs/reference/standard-sql/data-definition-language#create_function_statement
create function mydataset.multiply_inputs(x float64, y float64)
returns float64
as (x * y)
;

create temp function multiplyinputs(x float64, y float64)
returns float64
language js
as r"""
  return x*y;
"""
;

select multiplyinputs(a, b)
from (select 3 as a, 2 as b)
;

create function mydataset.remote_multiply_inputs(x float64, y float64)
returns float64
remote with connection us.myconnection
options (endpoint = "https://us-central1-myproject.cloudfunctions.net/multiply")
;

create or replace table function mydataset.names_by_year(y int64)
as
select year, name, sum(number) as total
from `bigquery-public-data.usa_names.usa_1910_current`
where year = y
group by year, name
;

create or replace table function mydataset.names_by_year(y int64)
returns table<name string, year int64, total int64>
as
select year, name, sum(number) as total
from `bigquery-public-data.usa_names.usa_1910_current`
where year = y
group by year, name
;
