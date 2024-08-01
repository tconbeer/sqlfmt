select
    foo
    as bar,
    exists (
        select
            1
        from
            baz
        where
            qux
            = quux
    )
    as foo1,
    case
        when
            something
        then
            this
        else
            also
    end
    as more
from
    bar1
)))))__SQLFMT_OUTPUT__(((((
select
    foo as bar,
    exists (select 1 from baz where qux = quux) as foo1,
    case when something then this else also end as more
from bar1
