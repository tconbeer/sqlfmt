create or replace external function local_echo(string_col varchar)
    returns variant
    api_integration = demonstration_external_api_integration_01
    as 'https://xyz.execute-api.us-west-2.amazonaws.com/prod/remote_echo';

create secure external function fooooobarrrrr(string_col varchar, int_col int)
    returns variant
    returns null on null input
    immutable
    comment = 'who knows what this will do!?'
    api_integration = bar
    headers = (
    'volume-measure' = 'liters',
    'distance-measure' = 'kilometers'
    )
    context_headers = (current_timestamp)
    compression=gzip
    as 'https://www.example.com/snowflake-external-function'
;
alter function foo set comment = 'something quite long! something quite long! something quite long!';
ALTER FUNCTION foo set api_integration = baz;
)))))__SQLFMT_OUTPUT__(((((
create or replace external function local_echo(string_col varchar)
returns variant
api_integration = demonstration_external_api_integration_01
as 'https://xyz.execute-api.us-west-2.amazonaws.com/prod/remote_echo'
;

create secure external function fooooobarrrrr(string_col varchar, int_col int)
returns variant
returns null on null input
immutable
comment = 'who knows what this will do!?'
api_integration = bar
headers = ('volume-measure' = 'liters', 'distance-measure' = 'kilometers')
context_headers = (current_timestamp)
compression = gzip
as 'https://www.example.com/snowflake-external-function'
;
alter function foo
set comment = 'something quite long! something quite long! something quite long!'
;
alter function foo
set api_integration = baz
;
