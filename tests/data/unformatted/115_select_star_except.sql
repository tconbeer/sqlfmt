select * except (field_a, field_b, field_c), field_a::int as field_a, field_b::varchar as field_b, field_c::decimal(10,2) as field_c
from my_table
;
select * except (really_long_field_a, really_long_field_b, really_long_field_c, really_long_field_d), really_long_field_a::int as field_a
from my_table
;
select * exclude (field_a, field_b, field_c), field_a::int as field_a, field_b::varchar as field_b, field_c::decimal(10,2) as field_c
;
select * replace (really_long_field_a as really_long_field_b, really_long_field_c as really_long_field_d)
;
)))))__SQLFMT_OUTPUT__(((((
select
    * except (field_a, field_b, field_c),
    field_a::int as field_a,
    field_b::varchar as field_b,
    field_c::decimal(10, 2) as field_c
from my_table
;
select
    * except (
        really_long_field_a,
        really_long_field_b,
        really_long_field_c,
        really_long_field_d
    ),
    really_long_field_a::int as field_a
from my_table
;
select
    * exclude (field_a, field_b, field_c),
    field_a::int as field_a,
    field_b::varchar as field_b,
    field_c::decimal(10, 2) as field_c
;
select
    * replace (
        really_long_field_a as really_long_field_b,
        really_long_field_c as really_long_field_d
    )
;
