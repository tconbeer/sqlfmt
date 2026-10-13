-- https://github.com/tconbeer/sqlfmt/issues/636
SELECT ${myvar}, ${hivevar:Region_Name} AS region
FROM ${hivevar:schema}.orders
WHERE dt = '${hiveconf:run_date}' AND id = ${env:USER_ID} AND n > ${spark.sql.shuffle.partitions}
)))))__SQLFMT_OUTPUT__(((((
-- https://github.com/tconbeer/sqlfmt/issues/636
select ${myvar}, ${hivevar:Region_Name} as region
from ${hivevar:schema}.orders
where
    dt = '${hiveconf:run_date}'
    and id = ${env:USER_ID}
    and n > ${spark.sql.shuffle.partitions}
