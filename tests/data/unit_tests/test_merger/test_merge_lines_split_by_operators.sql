select
    a_field
    + another_field
    + another_field
    + another_field
    + another_field,
    b_field
    * another_field
    * another_field
    * another_field
    * another_field,
    c_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field,
    c_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    and another_field,
    d_field
    ,
    e_field,
    foofoofoofoofoofoofoofoofoofoo
    / barbarbarbarbarbarbar
    + foofoofoofoofoofoofoofoofoofoo
    / bazbazbazbazbazbaz
    + foofoofoofoofoofoofoofoofoofoo
    / quxquxquxquxqux,
    foofoofoofoofoofoofoofoofoofoo
    ^ barbarbarbarbarbarbar
    * foofoofoofoofoofoofoofoofoofoo
    ^ bazbazbazbazbazbaz
    * foofoofoofoofoofoofoofoofoofoo
    ^ quxquxquxquxqux
where
    something
    < something_else
    and another_thing
    = another_thing_entirely
    or maybe_something_completely_different
    and (
        something_something
        = 'Some Literal'
        or (
            foo 
            = 'another literal'
            and bar
            = 'something else'
        )
    )
    and foo_bar
    <> 0
)))))__SQLFMT_OUTPUT__(((((
select
    a_field + another_field + another_field + another_field + another_field,
    b_field * another_field * another_field * another_field * another_field,
    c_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field,
    c_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    + another_field
    and another_field,
    d_field,
    e_field,
    foofoofoofoofoofoofoofoofoofoo / barbarbarbarbarbarbar
    + foofoofoofoofoofoofoofoofoofoo / bazbazbazbazbazbaz
    + foofoofoofoofoofoofoofoofoofoo / quxquxquxquxqux,
    foofoofoofoofoofoofoofoofoofoo ^ barbarbarbarbarbarbar
    * foofoofoofoofoofoofoofoofoofoo ^ bazbazbazbazbazbaz
    * foofoofoofoofoofoofoofoofoofoo ^ quxquxquxquxqux
where
    something < something_else
    and another_thing = another_thing_entirely
    or maybe_something_completely_different
    and (
        something_something = 'Some Literal'
        or (foo = 'another literal' and bar = 'something else')
    )
    and foo_bar <> 0
