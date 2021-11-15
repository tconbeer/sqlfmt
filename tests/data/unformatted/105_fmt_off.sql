select a, 

b, c
-- fmt: off
FROM

SHOUTING_TABLE
--fmt: on
where 
    something_is_true
group by

a
)))))__SQLFMT_OUTPUT__(((((
select a, b, c
-- fmt: off
FROM

SHOUTING_TABLE
--fmt: on
where something_is_true
group by a