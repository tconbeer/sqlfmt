select
    /* this
    is a multiline comment
    followed by another token
    that should be on a new line */ a,
    {{ my_aliased_macro(
        first_arg = 'one',
        second_arg = 'two',
    ) }} as b,
    {{ my_unaliased_macro(
        first_arg = 'one',
        second_arg = 'two',
    ) }},
    c

from my_table