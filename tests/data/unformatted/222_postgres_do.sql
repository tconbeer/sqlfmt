DO $$
BEGIN
 IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sales_interval_type' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'common')) THEN
 create type common.sales_interval_type as (l36 REAL, l24 REAL, l12 REAL);
 END IF;
END$$;
)))))__SQLFMT_OUTPUT__(((((
do
$$
begin
if
    not exists (
        select 1
        from pg_type
        where
            typname = 'sales_interval_type'
            and typnamespace = (select oid from pg_namespace where nspname = 'common')
    )
then create type common.sales_interval_type as (l36 real, l24 real, l12 real)
;
end
if
;
end
$$
;
