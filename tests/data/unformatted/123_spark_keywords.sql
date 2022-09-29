SELECT * FROM test TABLESAMPLE (50 PERCENT);
SELECT * FROM a_super_duper_really_very_long_long_long_long_table_name TABLESAMPLE (BUCKET 4 OUT OF 10);
SELECT age, name FROM person CLUSTER BY age;
SELECT foooooooooooooooooooooooooo, barrrrrrrrrrrrrrrrrrrrrrrrrrrr, bazzzzzzzzzzzzzzzzzzzzzzzzzz, quxxxxxxxxxxxxxxxxxxxxxxxxxx FROM person CLUSTER BY foooooooooooooooooooooooooo, barrrrrrrrrrrrrrrrrrrrrrrrrrrr, bazzzzzzzzzzzzzzzzzzzzzzzzzz, quxxxxxxxxxxxxxxxxxxxxxxxxxx;
SELECT age, name FROM person Distribute BY age;
SELECT foooooooooooooooooooooooooo, barrrrrrrrrrrrrrrrrrrrrrrrrrrr, bazzzzzzzzzzzzzzzzzzzzzzzzzz, quxxxxxxxxxxxxxxxxxxxxxxxxxx FROM person distribute BY foooooooooooooooooooooooooo, barrrrrrrrrrrrrrrrrrrrrrrrrrrr, bazzzzzzzzzzzzzzzzzzzzzzzzzz, quxxxxxxxxxxxxxxxxxxxxxxxxxx;
SELECT age, name FROM person sorT BY age;
SELECT foooooooooooooooooooooooooo, barrrrrrrrrrrrrrrrrrrrrrrrrrrr, bazzzzzzzzzzzzzzzzzzzzzzzzzz, quxxxxxxxxxxxxxxxxxxxxxxxxxx FROM person Sort BY foooooooooooooooooooooooooo, barrrrrrrrrrrrrrrrrrrrrrrrrrrr, bazzzzzzzzzzzzzzzzzzzzzzzzzz, quxxxxxxxxxxxxxxxxxxxxxxxxxx;
SELECT * FROM person
    PIVOT (
        SUM(age) AS a, AVG(class) AS c
        FOR name IN ('John' AS john, 'Mike' AS mike)
    );
SELECT * FROM person
PIVOT (
        SUM(age) AS a, AVG(class) AS c
        FOR (name, age) IN (('John', 30) AS c1, ('Mike', 40) AS c2)
    );
SELECT * FROM person
    LATERAL VIEW EXPLODE(ARRAY(30, 60)) tableName AS c_age
    LATERAL VIEW EXPLODE(ARRAY(40, 80)) AS d_age;
SELECT * FROM person
    LATERAL VIEW OUTER EXPLODE(ARRAY()) tableName AS c_age;
)))))__SQLFMT_OUTPUT__(((((
select *
from test tablesample (50 percent)
;
select *
from
    a_super_duper_really_very_long_long_long_long_table_name
    tablesample (bucket 4 out of 10)
;
select age, name
from person
cluster by age
;
select
    foooooooooooooooooooooooooo,
    barrrrrrrrrrrrrrrrrrrrrrrrrrrr,
    bazzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxx
from person
cluster by
    foooooooooooooooooooooooooo,
    barrrrrrrrrrrrrrrrrrrrrrrrrrrr,
    bazzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxx
;
select age, name
from person
distribute by age
;
select
    foooooooooooooooooooooooooo,
    barrrrrrrrrrrrrrrrrrrrrrrrrrrr,
    bazzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxx
from person
distribute by
    foooooooooooooooooooooooooo,
    barrrrrrrrrrrrrrrrrrrrrrrrrrrr,
    bazzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxx
;
select age, name
from person
sort by age
;
select
    foooooooooooooooooooooooooo,
    barrrrrrrrrrrrrrrrrrrrrrrrrrrr,
    bazzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxx
from person
sort by
    foooooooooooooooooooooooooo,
    barrrrrrrrrrrrrrrrrrrrrrrrrrrr,
    bazzzzzzzzzzzzzzzzzzzzzzzzzz,
    quxxxxxxxxxxxxxxxxxxxxxxxxxx
;
select *
from
    person
    pivot (sum(age) as a, avg(class) as c for name in ('John' as john, 'Mike' as mike))
;
select *
from
    person pivot (
        sum(age) as a,
        avg(class) as c
        for(name, age) in (('John', 30) as c1, ('Mike', 40) as c2)
    )
;
select *
from person
lateral view explode(array(30, 60)) tablename as c_age
lateral view explode(array(40, 80)) as d_age
;
select *
from person
lateral view outer explode(array()) tablename as c_age
;
