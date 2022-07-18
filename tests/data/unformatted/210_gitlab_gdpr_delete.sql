# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE: https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
WITH email_columns AS (

    SELECT 
        LOWER(table_catalog)||'.'||LOWER(table_schema)||'.'||LOWER(table_name) AS fqd_name,
        LISTAGG(column_name,',') AS email_column_names
    FROM "RAW"."INFORMATION_SCHEMA"."COLUMNS"
    WHERE LOWER(column_name) LIKE '%email%'
        AND table_schema IN ('SNAPSHOTS')
        AND data_type NOT IN {{data_types}}
        AND LOWER(column_name) NOT IN {{exclude_columns}}
        AND LOWER(table_name) LIKE ('gitlab_dotcom_%')
    GROUP BY 1

), non_email_columns AS (

    SELECT 
        LOWER(table_catalog)||'.'||LOWER(table_schema)||'.'||LOWER(table_name) AS fqd_name,
        LISTAGG(column_name,',') AS non_email_column_names
    FROM "RAW"."INFORMATION_SCHEMA"."COLUMNS" AS a
    WHERE LOWER(column_name) NOT LIKE '%email%'
        AND table_schema IN ('SNAPSHOTS')
        AND data_type NOT IN {{data_types}}
        AND LOWER(column_name) NOT IN {{exclude_columns}}
        AND LOWER(column_name) NOT LIKE '%id%'
        AND LOWER(column_name) NOT IN {{exclude_columns}}
        AND LOWER(table_name) LIKE ('gitlab_dotcom_%')
    GROUP BY 1

)

SELECT
    a.fqd_name, 
    a.email_column_names, 
    b.non_email_column_names
FROM email_columns a
LEFT JOIN non_email_columns b ON a.fqd_name = b.fqd_name
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE:
# https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
with
    email_columns as (

        select
            lower(table_catalog)
            || '.'
            || lower(table_schema)
            || '.'
            || lower(table_name) as fqd_name,
            listagg(column_name, ',') as email_column_names
        from "RAW"."INFORMATION_SCHEMA"."COLUMNS"
        where
            lower(column_name) like '%email%'
            and table_schema in ('SNAPSHOTS')
            and data_type not in {{ data_types }}
            and lower(column_name) not in {{ exclude_columns }}
            and lower(table_name) like ('gitlab_dotcom_%')
        group by 1

    ),
    non_email_columns as (

        select
            lower(table_catalog)
            || '.'
            || lower(table_schema)
            || '.'
            || lower(table_name) as fqd_name,
            listagg(column_name, ',') as non_email_column_names
        from "RAW"."INFORMATION_SCHEMA"."COLUMNS" as a
        where
            lower(column_name) not like '%email%'
            and table_schema in ('SNAPSHOTS')
            and data_type not in {{ data_types }}
            and lower(column_name) not in {{ exclude_columns }}
            and lower(column_name) not like '%id%'
            and lower(column_name) not in {{ exclude_columns }}
            and lower(table_name) like ('gitlab_dotcom_%')
        group by 1

    )

select a.fqd_name, a.email_column_names, b.non_email_column_names
from email_columns a
left join non_email_columns b on a.fqd_name = b.fqd_name
