# COPYRIGHT HTTP ARCHIVE
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/tconbeer/http_archive_almanac/blob/a57e75a9d37e150cb7963b821d9a33ad3d651571/LICENSE
# standardSQL
# 02_37: Distribution of unique z-index values per page
create temporary function getzindexvalues(css string)
returns array
< string
> language js
as '''
try {
  var reduceValues = (values, rule) => {
    if ('rules' in rule) {
      return rule.rules.reduce(reduceValues, values);
    }
    if (!('declarations' in rule)) {
      return values;
    }

    return values.concat(rule.declarations.filter(d => d.property.toLowerCase() == 'z-index' && !isNaN(parseInt(d.value))).map(d => parseInt(d.value)));
  };
  var $ = JSON.parse(css);
  return $.stylesheet.rules.reduce(reduceValues, []);
} catch (e) {
  return [];
}
'''
;

SELECT
    client, approx_quantiles(zindices, 1000)[offset(100)] as p10,
    approx_quantiles(zindices, 1000)[offset(250)] as p25, approx_quantiles(zindices, 1000)[offset(500)] as p50,
    approx_quantiles(zindices, 1000)[offset(750)] as p75, approx_quantiles(zindices, 1000)[offset(900)] as p90
FROM
    (
        select client, count(distinct value) as zindices
        from `httparchive.almanac.parsed_css`
        left join unnest(getzindexvalues(css)) as value
        where date = '2019-07-01'
        group by client, page
    )
GROUP BY client
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT HTTP ARCHIVE
# LICENSED UNDER APACHE 2.0
# SEE: 
# https://github.com/tconbeer/http_archive_almanac/blob/a57e75a9d37e150cb7963b821d9a33ad3d651571/LICENSE
# standardSQL
# 02_37: Distribution of unique z-index values per page
create temporary function getzindexvalues(css string)
returns array
< string
> language js
as '''
try {
  var reduceValues = (values, rule) => {
    if ('rules' in rule) {
      return rule.rules.reduce(reduceValues, values);
    }
    if (!('declarations' in rule)) {
      return values;
    }

    return values.concat(rule.declarations.filter(d => d.property.toLowerCase() == 'z-index' && !isNaN(parseInt(d.value))).map(d => parseInt(d.value)));
  };
  var $ = JSON.parse(css);
  return $.stylesheet.rules.reduce(reduceValues, []);
} catch (e) {
  return [];
}
'''
;

select
    client,
    approx_quantiles(zindices, 1000)[offset(100)] as p10,
    approx_quantiles(zindices, 1000)[offset(250)] as p25,
    approx_quantiles(zindices, 1000)[offset(500)] as p50,
    approx_quantiles(zindices, 1000)[offset(750)] as p75,
    approx_quantiles(zindices, 1000)[offset(900)] as p90
from
    (
        select client, count(distinct value) as zindices
        from `httparchive.almanac.parsed_css`
        left join unnest(getzindexvalues(css)) as value
        where date = '2019-07-01'
        group by client, page
    )
group by client
