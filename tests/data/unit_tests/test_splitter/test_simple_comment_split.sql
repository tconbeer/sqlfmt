select -- not distinct, just an ordinary select here, no big deal at all, it's okay really
    my_first_field + an_operation, -- here is a long comment to be wrapped above this line
    my_second_field, -- a short comment
    -- standalone for third
    my_third_field + another_long_operation -- here is another long comment to be wrapped but not indented
from my_really_long_data_source -- another comment that is a little bit too long to stay here
where -- this should stay
    true
-- one last comment
)))))__SQLFMT_OUTPUT__(((((
select
    my_first_field
    + an_operation,
    my_second_field,
    my_third_field
    + another_long_operation
from
    my_really_long_data_source
where
    true
    
