select
    ARRAY_AGG(DISTINCT foobar.my_special_foo) WITHIN GROUP (ORDER BY foobar.another_foo)    AS a_very_long_alias,
    ARRAY_AGG(DISTINCT foobar.my_special_foo || foobar.another_very_long_foo) WITHIN GROUP (ORDER BY foobar.another_foo desc)    AS a_very_long_alias,
    ARRAY_AGG(DISTINCT foobar.my_special_foo) WITHIN GROUP (ORDER BY foobar.another_foo) FILTER (WHERE barbar = "bazbaz" and bazbaz = "quxqux")   AS something_else,
    ARRAY_AGG(DISTINCT foobar.my_special_foo) WITHIN GROUP (ORDER BY foobar.another_foo) FILTER (WHERE barbar = "bazbaz" and bazbaz = "quxqux" and something_else_quite_long = "a long literal")   AS something_else
from my_table as foobar
)))))__SQLFMT_OUTPUT__(((((
select
    array_agg(distinct foobar.my_special_foo) within group (
        order by foobar.another_foo
    ) as a_very_long_alias,
    array_agg(
        distinct foobar.my_special_foo || foobar.another_very_long_foo
    ) within group (order by foobar.another_foo desc) as a_very_long_alias,
    array_agg(distinct foobar.my_special_foo) within group (
        order by foobar.another_foo
    ) filter (where barbar = "bazbaz" and bazbaz = "quxqux") as something_else,
    array_agg(distinct foobar.my_special_foo) within group (
        order by foobar.another_foo
    ) filter (
        where
            barbar = "bazbaz"
            and bazbaz = "quxqux"
            and something_else_quite_long = "a long literal"
    ) as something_else
from my_table as foobar
