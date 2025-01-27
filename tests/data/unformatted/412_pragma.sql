-- source: https://duckdb.org/docs/configuration/pragmas.html
PRAGMA collations;
SET threads = 4;
SET default_collation = 'nocase';
SET default_null_order = 'NULLS_FIRST';
SET default_null_order = 'NULLS_LAST_ON_ASC_FIRST_ON_DESC';
PRAGMA default_collation = 'nocase';
PRAGMA default_null_order = 'NULLS_FIRST';
PRAGMA default_null_order = 'NULLS_LAST_ON_ASC_FIRST_ON_DESC';
PRAGMA order_by_non_integer_literal = true;
PRAGMA version;
CALL pragma_version();
PRAGMA enable_progress_bar;
PRAGMA explain_output = 'physical_only';
PRAGMA table_info('table_name');
CALL pragma_table_info('table_name');
)))))__SQLFMT_OUTPUT__(((((
-- source: https://duckdb.org/docs/configuration/pragmas.html
pragma collations
;
set threads = 4
;
set default_collation = 'nocase'
;
set default_null_order = 'NULLS_FIRST'
;
set default_null_order = 'NULLS_LAST_ON_ASC_FIRST_ON_DESC'
;
pragma default_collation = 'nocase'
;
pragma default_null_order = 'NULLS_FIRST'
;
pragma default_null_order = 'NULLS_LAST_ON_ASC_FIRST_ON_DESC'
;
pragma order_by_non_integer_literal = true
;
pragma version
;
call pragma_version()
;
pragma enable_progress_bar
;
pragma explain_output = 'physical_only'
;
pragma table_info('table_name')
;
call pragma_table_info('table_name')
;
