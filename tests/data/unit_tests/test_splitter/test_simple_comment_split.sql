select -- not distinct, just an ordinary select here, no big deal at all, it's okay really
    my_first_field + an_operation, -- here is a long comment to be wrapped above this line
    my_second_field, -- a short comment
    my_third_field + another_long_operation -- here is another long comment to be wrapped but not indented
from my_really_long_data_source -- another comment that is a little bit too long to stay here
where -- this should stay
    true
-- one last comment
)))))__SQLFMT_OUTPUT__(((((
-- not distinct, just an ordinary select here, no big deal at all, it's okay really
select
    -- here is a long comment to be wrapped above this line
    my_first_field + an_operation,
    my_second_field, -- a short comment
    -- here is another long comment to be wrapped but not indented
    my_third_field + another_long_operation
    -- another comment that is a little bit too long to stay here
from
    my_really_long_data_source
where -- this should stay
    true
    -- one last comment