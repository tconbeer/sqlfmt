-- source: https://github.com/tconbeer/sqlfmt/issues/395
-- for now this should no-op
CREATE OR REPLACE VIEW someview AS (
WITH some_cte AS (SELECT CASE WHEN foo = bar THEN 1 ELSE 0 END AS biz FROM BAT)
select * from some_cte
)
