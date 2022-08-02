# COPYRIGHT HTTP ARCHIVE
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/tconbeer/http_archive_almanac/blob/a57e75a9d37e150cb7963b821d9a33ad3d651571/LICENSE
# 14_02: AMP plugin mode
SELECT
  client,
  amp_plugin_mode,
  COUNT(DISTINCT url) AS freq,
  SUM(COUNT(DISTINCT url)) OVER (PARTITION BY client) AS total,
  ROUND(COUNT(DISTINCT url) * 100 / SUM(COUNT(DISTINCT url)) OVER (PARTITION BY client), 2) AS pct
FROM (
  SELECT
    client,
    page AS url,
    SPLIT(REGEXP_EXTRACT(body, '(?i)<meta[^>]+name=[\'"]?generator[^>]+content=[\'"]?AMP Plugin v(\\d+\\.\\d+[^\'">]*)'), ';')[SAFE_OFFSET(1)] AS amp_plugin_mode
  FROM
    `httparchive.almanac.summary_response_bodies`
  WHERE
    date = '2019-07-01' AND
    firstHtml)
INNER JOIN
  (SELECT _TABLE_SUFFIX AS client, url FROM `httparchive.technologies.2019_07_01_*` WHERE app = 'WordPress')
USING
  (client, url)
GROUP BY
  client,
  amp_plugin_mode
ORDER BY
  freq / total DESC
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT HTTP ARCHIVE
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/tconbeer/http_archive_almanac/blob/a57e75a9d37e150cb7963b821d9a33ad3d651571/LICENSE
# 14_02: AMP plugin mode
select
    client,
    amp_plugin_mode,
    count(distinct url) as freq,
    sum(count(distinct url)) over (partition by client) as total,
    round(
        count(distinct url) * 100 / sum(count(distinct url)) over (partition by client),
        2
    ) as pct
from
    (
        select
            client,
            page as url,
            split(
                regexp_extract(
                    body,
                    '(?i)<meta[^>]+name=[\'"]?generator[^>]+content=[\'"]?AMP Plugin v(\\d+\\.\\d+[^\'">]*)'
                ),
                ';'
            )[safe_offset(1)] as amp_plugin_mode
        from `httparchive.almanac.summary_response_bodies`
        where date = '2019-07-01' and firsthtml
    )
inner join
    (
        select _table_suffix as client, url
        from `httparchive.technologies.2019_07_01_*`
        where app = 'WordPress'
    ) using (client, url)
group by client, amp_plugin_mode
order by freq / total desc
