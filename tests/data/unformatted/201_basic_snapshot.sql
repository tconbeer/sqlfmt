{% snapshot snp_my_snapshot %}
{{
    config(
          target_database='analytics',
          target_schema=target.schema + '_snapshots',
          unique_key='id',
          strategy='timestamp',
          updated_at='updated_at',
        )
}}

select * from {{ ref('stg_my_model') }}{% endsnapshot %}
)))))__SQLFMT_OUTPUT__(((((
{% snapshot snp_my_snapshot %}
{{
    config(
        target_database="analytics",
        target_schema=target.schema + "_snapshots",
        unique_key="id",
        strategy="timestamp",
        updated_at="updated_at",
    )
}} select * from {{ ref("stg_my_model") }}
{% endsnapshot %}
