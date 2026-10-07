select e.id, mgr.id as manager_id
from employees e
join employees mgr on e.manager_id = mgr.id
)))))__SQLFMT_OUTPUT__(((((
select e.id, mgr.id as manager_id

from employees e
inner join employees mgr
    on e.manager_id = mgr.id
