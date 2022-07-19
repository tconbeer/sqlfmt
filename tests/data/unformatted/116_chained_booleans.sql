select *
from historic_answers ha
where 1=1
    and subject = 'Math' 
    and learningobjective = "Addition" 
    and dt_utc > date('2020-10-01') 
    and testschool = false
)))))__SQLFMT_OUTPUT__(((((
select *
from historic_answers ha
where
    1 = 1
    and subject = 'Math'
    and learningobjective = "Addition"
    and dt_utc > date('2020-10-01')
    and testschool = false
