select a from t1
union
select a from t2
union all
select a from t3
intersect
select a from t4
except
select a from t5
)))))__SQLFMT_OUTPUT__(((((
select a

from t1

union

select a

from t2

union all

select a

from t3

intersect

select a

from t4

except

select a

from t5
