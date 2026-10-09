{{ config(materialized='incremental', unique_key='id', tags=['finance','daily'], on_schema_change='append_new_columns') }}
with
    a as (select * from b)
select * from a
)))))__SQLFMT_OUTPUT__(((((
{{
    config(
        materialized="incremental",
        unique_key="id",
        tags=["finance", "daily"],
        on_schema_change="append_new_columns",
    )
}}

with

a as (

    select * from b

)

select * from a
