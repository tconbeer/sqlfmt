select one.one, two.two, 
three.three, four.four, five.five, six.six, seven.seven
from one
join two on one.two = two.one
inner join "my_database"."my_schema".three as three on one.three = three.one
left outer join four on
    one.four = four.one and two.four = four.two 
        and three.four = four.three 
        and something_else
right join (
    select id, five, six, seven, eight, nine 
    from my_table where some_filter is true
) as five using(five.id)
natural full outer join six
left anti join seven on one.seven = seven.one
cross join {{ ref('bar_bar_bar') }} as bar
)))))__SQLFMT_OUTPUT__(((((
select one.one, two.two, three.three, four.four, five.five, six.six, seven.seven
from one
join two on one.two = two.one
inner join "my_database"."my_schema".three as three on one.three = three.one
left outer join
    four
    on one.four = four.one
    and two.four = four.two
    and three.four = four.three
    and something_else
right join
    (
        select id, five, six, seven, eight, nine from my_table where some_filter is true
    ) as five using (five.id)
natural full outer join six
left anti join seven on one.seven = seven.one
cross join {{ ref("bar_bar_bar") }} as bar
