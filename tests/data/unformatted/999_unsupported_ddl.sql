CREATE PUBLICATION insert_only FOR TABLE mydata
    WITH (publish = 'insert');
CREATE PUBLICATION production_publication FOR TABLE users, departments, TABLES IN SCHEMA production;
CREATE PUBLICATION users_filtered FOR TABLE users (user_id, firstname);
create table foo as (
    aaa text,
    "bBb" int,
    ccc date
);
SELECT
    1;
)))))__SQLFMT_OUTPUT__(((((
CREATE PUBLICATION insert_only FOR TABLE mydata
    WITH (publish = 'insert');
CREATE PUBLICATION production_publication FOR TABLE users, departments, TABLES IN SCHEMA production;
CREATE PUBLICATION users_filtered FOR TABLE users (user_id, firstname);
create table foo as (
    aaa text,
    "bBb" int,
    ccc date
);
select 1
;
