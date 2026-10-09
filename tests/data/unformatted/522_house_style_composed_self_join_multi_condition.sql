select e.id, mgr.id as manager_id, recent.total
from employees as e
join employees as mgr on e.manager_id = mgr.id and mgr.active = true and mgr.region = e.region
left outer join (
    select employee_id, sum(amount) as total
    from orders
    group by employee_id
) as recent on recent.employee_id = e.id
)))))__SQLFMT_OUTPUT__(((((
select
    e.id,
    mgr.id as manager_id,
    recent.total

from employees e

inner join employees mgr
    on e.manager_id = mgr.id
    and mgr.active = true
    and mgr.region = e.region

left join
    (

        select
            employee_id,
            sum(amount) as total

        from orders

        group by employee_id

    ) recent
    on recent.employee_id = e.id
