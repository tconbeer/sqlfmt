-- https://github.com/tconbeer/sqlfmt/issues/657
SELECT coalesce(*COLUMNS(['a', 'b', 'c'])) AS result
)))))__SQLFMT_OUTPUT__(((((
-- https://github.com/tconbeer/sqlfmt/issues/657
select coalesce(*columns(['a', 'b', 'c'])) as result
