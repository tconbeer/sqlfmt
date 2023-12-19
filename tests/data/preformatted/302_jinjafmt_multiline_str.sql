{{
    config(
        materialized="incremental",
        pre_hook="""
            delete from
                dwh.user as t using (
                select distinct campaign_name, date
                from datalake.conversion
                where date_part = date('{{ execution_date }}')
            ) as s
            where
                t.campaign_name = s.campaign_name
                and to_date(t.imported_at) <= s.date_part
            """,
    )
}}

select campaign_name, date_part, count(distinct user_id) as users
