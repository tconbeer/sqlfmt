select
    case
        when something_is_true
        then do_this
        when someting_else_is_true
        then do_that
        else something
    end -- a really long comment that doesn't belong here at all but will cause bracket issues
from (
    select * from my_table
) -- another really long comment that doesn't belong here at all but will cause bracket issues
)))))__SQLFMT_OUTPUT__(((((
select
    case
        when
            something_is_true
        then
            do_this
        when
            someting_else_is_true
        then
            do_that
        else
            something
    end
from
    (
        select
            *
        from
            my_table
    )
