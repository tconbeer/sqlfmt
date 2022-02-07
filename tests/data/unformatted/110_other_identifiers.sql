select
    v.$1, v.$2
  from
    @my_stage( file_format => 'csv_format', pattern => '.*my_pattern.*') v
)))))__SQLFMT_OUTPUT__(((((
select v.$1, v.$2
from @my_stage(file_format => 'csv_format', pattern => '.*my_pattern.*') v
