select something
    , another_thing
    , and_another
    , *
    , sum(something) as something_else
    , and_another / 100 as alias
    , row_number() over (partition by something) as n
from my_table
)))))__SQLFMT_OUTPUT__(((((
select
    something,
    another_thing,
    and_another,
    *,
    sum(something) as something_else,
    and_another / 100 as alias,
    row_number() over (partition by something) as n
from my_table
