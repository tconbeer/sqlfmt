GRANT INSERT ON films TO PUBLIC;
GRANT ALL PRIVILEGES ON kinds TO manuel;
GRANT SELECT,
INSERT,
UPDATE,
DELETE,
TRUNCATE,
REFERENCES,
TRIGGER,
on table my_database.my_schema.my_table
to some_rather_long_role_name_foooooooooooo_barrrr, another_rather_long_role_name_foooooooooooo_barrrrrrrrrrrrr
with grant option
granted by some_admin_role;
revoke all privileges on all tables in schema my_schema
from old_role cascade;
revoke grant option for select, insert, update, delete, truncate, references, trigger
from old_admin_role;
select foo from bar where true
)))))__SQLFMT_OUTPUT__(((((
grant insert
on films
to public
;
grant all privileges
on kinds
to manuel
;
grant select, insert, update, delete, truncate, references, trigger,
on table my_database.my_schema.my_table
to
    some_rather_long_role_name_foooooooooooo_barrrr,
    another_rather_long_role_name_foooooooooooo_barrrrrrrrrrrrr
with grant option
granted by some_admin_role
;
revoke all privileges
on all tables in schema my_schema
from old_role
cascade
;
revoke grant option for select, insert, update, delete, truncate, references, trigger
from old_admin_role
;
select foo
from bar
where true
