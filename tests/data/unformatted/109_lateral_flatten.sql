select src:device_type::string
, src:version::string
, _airbyte_data:"AccountId"::varchar as accountid
, value
from
  raw_source
, lateral flatten( input => src:events );
)))))__SQLFMT_OUTPUT__(((((
select
    src:device_type::string,
    src:version::string,
    _airbyte_data:"AccountId"::varchar as accountid,
    value
from raw_source, lateral flatten(input => src:events)
;
