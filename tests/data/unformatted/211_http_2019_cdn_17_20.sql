# COPYRIGHT HTTP ARCHIVE
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/tconbeer/http_archive_almanac/blob/a57e75a9d37e150cb7963b821d9a33ad3d651571/LICENSE
# 17_20: Percentage of responses with s-maxage directive
SELECT
  _TABLE_SUFFIX AS client,
  IFNULL(NULLIF(REGEXP_EXTRACT(_cdn_provider, r'^([^,]*).*'), ''), 'ORIGIN') AS cdn,
  COUNTIF(LOWER(resp_cache_control) LIKE '%s-maxage%') AS freq,
  COUNTIF(firstHTML AND LOWER(resp_cache_control) LIKE '%s-maxage%') AS firstHtmlFreq,
  COUNTIF(NOT firstHtml AND LOWER(resp_cache_control) LIKE '%s-maxage%') AS resourceFreq,
  COUNT(0) AS total,
  ROUND(COUNTIF(LOWER(resp_cache_control) LIKE '%s-maxage%') * 100 / COUNT(0), 2) AS pct,
  ROUND(COUNTIF(firstHtml AND LOWER(resp_cache_control) LIKE '%s-maxage%') * 100 / COUNT(0), 2) AS firstHtmlPct,
  ROUND(COUNTIF(NOT firstHtml AND LOWER(resp_cache_control) LIKE '%s-maxage%') * 100 / COUNT(0), 2) AS ResourcePct
FROM
  `httparchive.summary_requests.2019_07_01_*`
GROUP BY
  client,
  cdn
ORDER BY
  client ASC,
  freq DESC
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT HTTP ARCHIVE
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/tconbeer/http_archive_almanac/blob/a57e75a9d37e150cb7963b821d9a33ad3d651571/LICENSE
# 17_20: Percentage of responses with s-maxage directive
select
    _table_suffix as client,
    ifnull(nullif(regexp_extract(_cdn_provider, r'^([^,]*).*'), ''), 'ORIGIN') as cdn,
    countif(lower(resp_cache_control) like '%s-maxage%') as freq,
    countif(firsthtml and lower(resp_cache_control) like '%s-maxage%') as firsthtmlfreq,
    countif(
        not firsthtml and lower(resp_cache_control) like '%s-maxage%'
    ) as resourcefreq,
    count(0) as total,
    round(
        countif(lower(resp_cache_control) like '%s-maxage%') * 100 / count(0), 2
    ) as pct,
    round(
        countif(firsthtml and lower(resp_cache_control) like '%s-maxage%')
        * 100
        / count(0),
        2
    ) as firsthtmlpct,
    round(
        countif(not firsthtml and lower(resp_cache_control) like '%s-maxage%')
        * 100
        / count(0),
        2
    ) as resourcepct
from `httparchive.summary_requests.2019_07_01_*`
group by client, cdn
order by client asc, freq desc
