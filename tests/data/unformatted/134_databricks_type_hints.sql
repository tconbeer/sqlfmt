-- see: https://github.com/tconbeer/sqlfmt/issues/639
-- source: https://docs.databricks.com/en/sql/language-manual/sql-ref-syntax-qry-select-hints.html
SELECT /*+ COALESCE(3) */ * FROM t;
SELECT /*+ REPARTITION(3) */ * FROM t;
SELECT /*+ REPARTITION(c) */ * FROM t;
SELECT /*+ REPARTITION(3, c) */ * FROM t;
SELECT /*+ REPARTITION_BY_RANGE(c) */ * FROM t;
SELECT /*+ REPARTITION_BY_RANGE(3, c) */ * FROM t;
SELECT /*+ BROADCAST(t1) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;
SELECT /*+ BROADCASTJOIN (t1) */ * FROM t1 left JOIN t2 ON t1.key = t2.key;
SELECT /*+ MAPJOIN(t2) */ * FROM t1 right JOIN t2 ON t1.key = t2.key;

-- Join Hints for shuffle sort merge join
SELECT /*+ SHUFFLE_MERGE(t1) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;
SELECT /*+ MERGEJOIN(t2) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;
SELECT /*+ MERGE(t1) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;

-- Join Hints for shuffle hash join
SELECT /*+ SHUFFLE_HASH(t1) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;

-- Join Hints for shuffle-and-replicate nested loop join
SELECT /*+ SHUFFLE_REPLICATE_NL(t1) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;
SELECT /*+ BROADCAST(t1), MERGE(t1, t2) */ * FROM t1 INNER JOIN t2 ON t1.key = t2.key;
)))))__SQLFMT_OUTPUT__(((((
-- see: https://github.com/tconbeer/sqlfmt/issues/639
-- source:
-- https://docs.databricks.com/en/sql/language-manual/sql-ref-syntax-qry-select-hints.html
select  /*+ COALESCE(3) */
    *
from t
;
select  /*+ REPARTITION(3) */
    *
from t
;
select  /*+ REPARTITION(c) */
    *
from t
;
select  /*+ REPARTITION(3, c) */
    *
from t
;
select  /*+ REPARTITION_BY_RANGE(c) */
    *
from t
;
select  /*+ REPARTITION_BY_RANGE(3, c) */
    *
from t
;
select  /*+ BROADCAST(t1) */
    *
from t1
inner join t2 on t1.key = t2.key
;
select  /*+ BROADCASTJOIN (t1) */
    *
from t1
left join t2 on t1.key = t2.key
;
select  /*+ MAPJOIN(t2) */
    *
from t1
right join t2 on t1.key = t2.key
;

-- Join Hints for shuffle sort merge join
select  /*+ SHUFFLE_MERGE(t1) */
    *
from t1
inner join t2 on t1.key = t2.key
;
select  /*+ MERGEJOIN(t2) */
    *
from t1
inner join t2 on t1.key = t2.key
;
select  /*+ MERGE(t1) */
    *
from t1
inner join t2 on t1.key = t2.key
;

-- Join Hints for shuffle hash join
select  /*+ SHUFFLE_HASH(t1) */
    *
from t1
inner join t2 on t1.key = t2.key
;

-- Join Hints for shuffle-and-replicate nested loop join
select  /*+ SHUFFLE_REPLICATE_NL(t1) */
    *
from t1
inner join t2 on t1.key = t2.key
;
select  /*+ BROADCAST(t1), MERGE(t1, t2) */
    *
from t1
inner join t2 on t1.key = t2.key
;
