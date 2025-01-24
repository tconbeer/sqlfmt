-- source: https://spark.apache.org/docs/latest/sql-ref-literals.html#integral-literal-syntax
-- see: https://github.com/tconbeer/sqlfmt/issues/640
SELECT -2147483648 AS col;
SELECT 9223372036854775807l AS col;
SELECT -32Y AS col;
SELECT 482S AS col;
SELECT 12.578 AS col;
SELECT -0.1234567 AS col;
SELECT -.1234567 AS col;
SELECT 123. AS col;
SELECT 123.BD AS col;
SELECT 5E2 AS col;
SELECT 5D AS col;
SELECT -5BD AS col;
SELECT 12.578e-2d AS col;
SELECT -.1234567E+2BD AS col;
SELECT +3.e+3 AS col;
SELECT -3.E-3D AS col;
)))))__SQLFMT_OUTPUT__(((((
-- source:
-- https://spark.apache.org/docs/latest/sql-ref-literals.html#integral-literal-syntax
-- see: https://github.com/tconbeer/sqlfmt/issues/640
select -2147483648 as col
;
select 9223372036854775807l as col
;
select -32y as col
;
select 482s as col
;
select 12.578 as col
;
select -0.1234567 as col
;
select -.1234567 as col
;
select 123. as col
;
select 123.bd as col
;
select 5e2 as col
;
select 5d as col
;
select -5bd as col
;
select 12.578e-2d as col
;
select -.1234567e+2bd as col
;
select +3.e+3 as col
;
select -3.e-3d as col
;
