select
    v.$1, v.$2, ?3, ?4
  from
    @my_stage( file_format => 'csv_format', pattern => '.*my_pattern.*') v
select
    METADATA$FILENAME AS file_name,
    METADATA$FILE_LAST_MODIFIED AS file_last_modified
  from
    @my_stage( file_format => 'csv_format', pattern => '.*my_pattern.*')
-- see: https://github.com/tconbeer/sqlfmt/issues/697
-- SparkSQL permits field names that start with a digit
select
    substring(f.9021_web_flag, 1, 11),
    f.1st_visit,
    9021_web_flag,
    f.1_000_flag
  from f
-- a number abutting a keyword must still split; these guard the lookahead
-- against being widened to (?!\w), which would lex 1as and 1and as one name
select 1as x from t
select 1 from t where x=1and y=2
select 1_000 + 2_000 from t
)))))__SQLFMT_OUTPUT__(((((
select v.$1, v.$2, ?3, ?4
from @my_stage(file_format => 'csv_format', pattern => '.*my_pattern.*') v
select metadata$filename as file_name, metadata$file_last_modified as file_last_modified
from @my_stage(file_format => 'csv_format', pattern => '.*my_pattern.*')
-- see: https://github.com/tconbeer/sqlfmt/issues/697
-- SparkSQL permits field names that start with a digit
select substring(f.9021_web_flag, 1, 11), f.1st_visit, 9021_web_flag, f.1_000_flag
from f
-- a number abutting a keyword must still split; these guard the lookahead
-- against being widened to (?!\w), which would lex 1as and 1and as one name
select 1 as x
from t
select 1
from t
where x = 1 and y = 2
select 1_000 + 2_000
from t
