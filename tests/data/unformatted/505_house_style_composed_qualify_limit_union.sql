(select a from t1 union select a from t2)
union all
select a
from t2
qualify row_number() over (partition by a order by a) = 1
limit 5
)))))__SQLFMT_OUTPUT__(((((
(
    select a

    from t1

    union

    select a

    from t2
)

union all

select a

from t2

qualify
    row_number() over (
        partition by a
        order by a
    )
    = 1

limit 5
