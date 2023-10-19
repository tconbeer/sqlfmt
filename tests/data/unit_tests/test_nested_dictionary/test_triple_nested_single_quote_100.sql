{{
    config(
        materialized='incremental',
        incremental_strategy='insert_overwrite',
        external_location=generate_external_location('baz', 'datalake/producer=foo/object=bar'),
        partitioned_by=['batch_date'],
        lf_tags_config={
            'enabled': true,
            'tags': {
                'nested_layer_0': 
        {'nested_layer_1':
        {'nested_layer_2':{'foo':'bar'}}},
                'domain': 'foo',
                'sensitivity': 'public',
            },
        },
    )
}}
select batch_date
from {{ ref("bar") }}
{% if is_incremental() %} where batch_date = '{{ var("ds") }}' {% endif %}
)))))__SQLFMT_OUTPUT__(((((
{{
    config(
        materialized="incremental",
        incremental_strategy="insert_overwrite",
        external_location=generate_external_location("baz", "datalake/producer=foo/object=bar"),
        partitioned_by=["batch_date"],
        lf_tags_config={
            "enabled": true,
            "tags": {
                "nested_layer_0": {"nested_layer_1": {"nested_layer_2": {"foo": "bar"}}},
                "domain": "foo",
                "sensitivity": "public",
            },
        },
    )
}}
select batch_date
from {{ ref("bar") }}
{% if is_incremental() %} where batch_date = '{{ var("ds") }}' {% endif %}
