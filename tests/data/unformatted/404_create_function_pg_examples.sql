-- COPYRIGHT POSTGRESQL
-- SEE https://www.postgresql.org/docs/15/sql-createfunction.html

CREATE FUNCTION add(integer, integer) RETURNS integer
    AS 'select $1 + $2;'
    LANGUAGE SQL
    IMMUTABLE
    RETURNS NULL ON NULL INPUT;

CREATE FUNCTION add(a integer, b integer) RETURNS integer
    LANGUAGE SQL
    IMMUTABLE
    RETURNS NULL ON NULL INPUT
    RETURN a + b;

CREATE OR REPLACE FUNCTION increment(i integer) RETURNS integer AS $$
        BEGIN
                RETURN i + 1;
        END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION dup(in int, out f1 int, out f2 text)
    AS $$ SELECT $1, CAST($1 AS text) || ' is text' $$
    LANGUAGE SQL;

CREATE FUNCTION dup(int) RETURNS dup_result
    AS $$ SELECT $1, CAST($1 AS text) || ' is text' $$
    LANGUAGE SQL;

CREATE FUNCTION check_password(uname TEXT, pass TEXT)
RETURNS BOOLEAN AS $$
DECLARE passed BOOLEAN;
BEGIN
        SELECT  (pwd = $2) INTO passed
        FROM    pwds
        WHERE   username = $1;

        RETURN passed;
END;
$$  LANGUAGE plpgsql
    SECURITY DEFINER
    -- Set a secure search_path: trusted schema(s), then 'pg_temp'.
    SET search_path = admin, pg_temp;
)))))__SQLFMT_OUTPUT__(((((
-- COPYRIGHT POSTGRESQL
-- SEE https://www.postgresql.org/docs/15/sql-createfunction.html
create function add(integer, integer)
returns integer
as 'select $1 + $2;'
language sql
immutable
returns null on null input
;

create function add(a integer, b integer)
returns integer
language sql
immutable
returns null on null input
return a + b
;

create or replace function increment(i integer)
returns integer
as $$
        BEGIN
                RETURN i + 1;
        END;
$$
language plpgsql
;

create function dup(in int, out f1 int, out f2 text)
as $$ SELECT $1, CAST($1 AS text) || ' is text' $$
language sql
;

create function dup(int)
returns dup_result
as $$ SELECT $1, CAST($1 AS text) || ' is text' $$
language sql
;

create function check_password(uname text, pass text)
returns boolean
as $$
DECLARE passed BOOLEAN;
BEGIN
        SELECT  (pwd = $2) INTO passed
        FROM    pwds
        WHERE   username = $1;

        RETURN passed;
END;
$$
language plpgsql
security definer
-- Set a secure search_path: trusted schema(s), then 'pg_temp'.
set search_path = admin, pg_temp
;
