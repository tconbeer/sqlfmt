select
    a,
    sum(a) over () as b,
    row_number() over () as c,
    count(case when a is null then 1 end) over (partition by user_id, date_trunc('year', performed_at)) as d,
    first_value(a ignore nulls) over (partition by user_id order by performed_at desc rows between unbounded preceding and unbounded following) as e
from
    my_table
)))))__SQLFMT_OUTPUT__(((((
select
    a,
    sum(a) over () as b,
    row_number() over () as c,
    count(case when a is null then 1 end) over (
        partition by user_id, date_trunc('year', performed_at)
    ) as d,
    first_value(a ignore nulls) over (
        partition by user_id 
        order by performed_at desc 
        rows between unbounded preceding and unbounded following
    ) as e
from my_table