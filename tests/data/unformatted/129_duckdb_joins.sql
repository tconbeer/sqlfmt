-- Source https://duckdb.org/docs/sql/query_syntax/from.html
-- Copyright DuckDB Foundation.

-- return a list of cars that have a valid region.
SELECT cars.name, cars.manufacturer 
FROM cars SEMI JOIN region
ON cars.region = region.id;
-- return a list of cars with no recorded safety data.
SELECT cars.name, cars.manufacturer
FROM cars ANTI JOIN safety_data
ON cars.safety_report_id = safety_data.report_id;
SELECT *
FROM range(3) t(i), LATERAL (SELECT i + 1) t2(j);
SELECT *
FROM generate_series(0, 1) t(i), LATERAL (SELECT i + 10 UNION ALL SELECT i + 100) t2(j);
CREATE TABLE t1 AS SELECT * FROM range(3) t(i), LATERAL (SELECT i + 1) t2(j);
SELECT * FROM t1, LATERAL (SELECT i + j) t2(k);
-- treat two data frames as a single table
SELECT df1.*, df2.*
FROM df1 POSITIONAL JOIN df2;
-- attach prices to stock trades
SELECT t.*, p.price
FROM trades t ASOF JOIN prices p 
  ON t.symbol = p.symbol AND t.created_at >= p.created_at;
  -- attach prices or NULLs to stock trades
SELECT *
FROM trades t ASOF LEFT JOIN prices p 
  ON t.symbol = p.symbol AND t.created_at >= p.created_at;
SELECT *
FROM trades t ASOF JOIN prices p USING (symbol, created_at);
-- Returns symbol, trades.created_at, price (but NOT prices.created_at)
SELECT t.symbol, t.created_at AS trade_when, p.created_at AS price_when, price
FROM trades t ASOF LEFT JOIN prices p USING (symbol, created_at);
)))))__SQLFMT_OUTPUT__(((((
-- Source https://duckdb.org/docs/sql/query_syntax/from.html
-- Copyright DuckDB Foundation.
-- return a list of cars that have a valid region.
select cars.name, cars.manufacturer
from cars
semi join region on cars.region = region.id
;
-- return a list of cars with no recorded safety data.
select cars.name, cars.manufacturer
from cars
anti join safety_data on cars.safety_report_id = safety_data.report_id
;
select *
from range(3) t(i), lateral(select i + 1) t2(j)
;
select *
from
    generate_series(0, 1) t(i),
    lateral(
        select i + 10
        union all
        select i + 100
    ) t2(j)
;
CREATE TABLE t1 AS SELECT * FROM range(3) t(i), LATERAL (SELECT i + 1) t2(j);
select *
from t1, lateral(select i + j) t2(k)
;
-- treat two data frames as a single table
select df1.*, df2.*
from df1
positional join df2
;
-- attach prices to stock trades
select t.*, p.price
from trades t
asof join prices p on t.symbol = p.symbol and t.created_at >= p.created_at
;
-- attach prices or NULLs to stock trades
select *
from trades t
asof left join prices p on t.symbol = p.symbol and t.created_at >= p.created_at
;
select *
from trades t
asof join prices p using (symbol, created_at)
;
-- Returns symbol, trades.created_at, price (but NOT prices.created_at)
select t.symbol, t.created_at as trade_when, p.created_at as price_when, price
from trades t
asof left join prices p using (symbol, created_at)
;
