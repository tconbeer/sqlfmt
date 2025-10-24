-- FROM https://clickhouse.com/docs/sql-reference/statements/select/join

SELECT expressions_list
FROM table_1
GLOBAL LEFT JOIN table_2
ON equi_cond AND closest_match_cond;

SELECT expressions_list
FROM table_1
ASOF LEFT JOIN table_2
ON equi_cond AND closest_match_cond;

SELECT expressions_list
FROM table_1
ASOF JOIN table_2
USING (equi_column1, equi_columnN, asof_column);

SELECT *
FROM
(
    SELECT number AS a
    FROM numbers(2)
) AS t1
PASTE JOIN
(
    SELECT number AS a
    FROM numbers(2)
    ORDER BY a DESC
) AS t2;

SELECT a, b, toTypeName(a), toTypeName(b) FROM t_1 FULL JOIN t_2 USING (a, b);

SELECT uniq(UserID) FROM distributed_table WHERE CounterID = 101500 AND UserID GLOBAL IN (SELECT UserID FROM distributed_table WHERE CounterID = 34);

SELECT
    CounterID,
    hits,
    visits
FROM
(
    SELECT
        CounterID,
        count() AS hits
    FROM test.hits
    GROUP BY CounterID
) ANY LEFT JOIN
(
    SELECT
        CounterID,
        sum(Sign) AS visits
    FROM test.visits
    GROUP BY CounterID
) USING CounterID
ORDER BY hits DESC
LIMIT 10;
)))))__SQLFMT_OUTPUT__(((((
-- FROM https://clickhouse.com/docs/sql-reference/statements/select/join
select expressions_list
from table_1
global left join table_2 on equi_cond and closest_match_cond
;

select expressions_list
from table_1
asof left join table_2 on equi_cond and closest_match_cond
;

select expressions_list
from table_1
asof join table_2 using (equi_column1, equi_columnn, asof_column)
;

select *
from (select number as a from numbers(2)) as t1
paste join (select number as a from numbers(2) order by a desc) as t2
;

select a, b, totypename(a), totypename(b)
from t_1
full join t_2 using (a, b)
;

select uniq(userid)
from distributed_table
where
    counterid = 101500
    and userid global in (select userid from distributed_table where counterid = 34)
;

select counterid, hits, visits
from (select counterid, count() as hits from test.hits group by counterid)
any left join
    (select counterid, sum(sign) as visits from test.visits group by counterid)
using counterid
order by hits desc
limit 10
;
