select * except (field_a, field_b, field_c), field_a::int as field_a, field_b::varchar as field_b, field_c::decimal(10,2) as field_c
from my_table
;
select * except (really_long_field_a, really_long_field_b, really_long_field_c, really_long_field_d), really_long_field_a::int as field_a
from my_table
;
select * exclude (field_a, field_b, field_c), field_a::int as field_a, field_b::varchar as field_b, field_c::decimal(10,2) as field_c
from my_table
;
select * replace (really_long_field_a as really_long_field_b, really_long_field_c as really_long_field_d),
replace(one_thing, another_thing, some_string)
from my_table
;
select
    recentagg_root.*
    except (recentagg),
    (
        select as struct
            recentagg.*,
            recentagg_topphases_array.topphases,
            recentagg_topsymptoms_array.topsymptoms,
            recentagg_toppositivesymptoms_array.toppositivesymptoms,
            recentagg_topactivities_array.topactivities,
    ) recentagg,
from recentagg_root
left join recentagg_topphases_array using (id)
left join recentagg_topsymptoms_array using (id)
left join recentagg_toppositivesymptoms_array using (id)
left join recentagg_topactivities_array using (id)
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
from my_table
;
select
    * replace (
        really_long_field_a as really_long_field_b,
        really_long_field_c as really_long_field_d
    ),
    replace(one_thing, another_thing, some_string)
from my_table
;
select
    recentagg_root.* except (recentagg),
    (
        select as struct
            recentagg.*,
            recentagg_topphases_array.topphases,
            recentagg_topsymptoms_array.topsymptoms,
            recentagg_toppositivesymptoms_array.toppositivesymptoms,
            recentagg_topactivities_array.topactivities,
    ) recentagg,
from recentagg_root
left join recentagg_topphases_array using (id)
left join recentagg_topsymptoms_array using (id)
left join recentagg_toppositivesymptoms_array using (id)
left join recentagg_topactivities_array using (id)
