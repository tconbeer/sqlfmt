-- COPYRIGHT POSTGRESQL.ORG
-- https://www.postgresql.org/docs/current/sql-alterfunction.html
ALTER FUNCTION sqrt(integer) RENAME TO square_root;
ALTER FUNCTION sqrt(integer) OWNER TO joe;
ALTER FUNCTION sqrt(integer) SET SCHEMA maths;
ALTER FUNCTION sqrt(integer) DEPENDS ON EXTENSION mathlib;
ALTER FUNCTION check_password(text) SET search_path = admin, pg_temp;
ALTER FUNCTION check_password(text) RESET search_path;
DROP FUNCTION sqrt(integer);
DROP FUNCTION square_root(integer), square_root(bigint), square_root(float), square_root(numeric), square_root(money) cascade;
DROP FUNCTION update_employee_salaries;
DROP FUNCTION update_employee_salaries();
)))))__SQLFMT_OUTPUT__(((((
-- COPYRIGHT POSTGRESQL.ORG
-- https://www.postgresql.org/docs/current/sql-alterfunction.html
alter function sqrt(integer)
rename to square_root
;
alter function sqrt(integer)
owner to joe
;
alter function sqrt(integer)
set schema maths
;
alter function sqrt(integer)
depends on extension mathlib
;
alter function check_password(text)
set search_path = admin, pg_temp
;
alter function check_password(text)
reset search_path
;
drop function sqrt(integer)
;
drop function
    square_root(integer),
    square_root(bigint),
    square_root(float),
    square_root(numeric),
    square_root(money)
cascade
;
drop function update_employee_salaries
;
drop function update_employee_salaries()
;
