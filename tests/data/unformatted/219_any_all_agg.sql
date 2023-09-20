
-- source: https://github.com/tconbeer/sqlfmt/issues/483
select any(number) as any_number from (select number from system.numbers limit 10);
select max(number) as max_number, min(number) as min_number, any(number) as any_number, avg(number) as avg_number from (select number from system.numbers limit 10);
select foo from bar where foo like all (baz) or foo like any (qux);
)))))__SQLFMT_OUTPUT__(((((
-- source: https://github.com/tconbeer/sqlfmt/issues/483
select any(number) as any_number
from (select number from system.numbers limit 10)
;
select
    max(number) as max_number,
    min(number) as min_number,
    any(number) as any_number,
    avg(number) as avg_number
from (select number from system.numbers limit 10)
;
select foo
from bar
where foo like all (baz) or foo like any (qux)
;
