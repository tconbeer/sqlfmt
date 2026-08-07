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
)))))__SQLFMT_OUTPUT__(((((
select v.$1, v.$2, ?3, ?4
from @my_stage(file_format => 'csv_format', pattern => '.*my_pattern.*') v
select metadata$filename as file_name, metadata$file_last_modified as file_last_modified
from @my_stage(file_format => 'csv_format', pattern => '.*my_pattern.*')
-- see: https://github.com/tconbeer/sqlfmt/issues/697
-- SparkSQL permits field names that start with a digit
select substring(f.9021_web_flag, 1, 11), f.1st_visit, 9021_web_flag, f.1_000_flag
from f
