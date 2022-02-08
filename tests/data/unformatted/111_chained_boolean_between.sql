select
    radio,
    mcc,
    net as mnc,
    area as lac,
    cell % 65536 as cid,
    cell / 65536 as rnc,
    cell as long_cid,
    lon,
    lat
from
    towershift
where
    radio != 'CDMA'
    and mcc between 200 and 799 and net between 1 and 999 and area between 0 and 65535
    and cell between 0 and 268435455 and lon between -180 and 180
    and lat between -90 and 90
)))))__SQLFMT_OUTPUT__(((((
select
    radio,
    mcc,
    net as mnc,
    area as lac,
    cell % 65536 as cid,
    cell / 65536 as rnc,
    cell as long_cid,
    lon,
    lat
from towershift
where
    radio != 'CDMA'
    and mcc between 200 and 799
    and net between 1 and 999
    and area between 0 and 65535
    and cell between 0 and 268435455
    and lon between -180 and 180
    and lat between -90 and 90
