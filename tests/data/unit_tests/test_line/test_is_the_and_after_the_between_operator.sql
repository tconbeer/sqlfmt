where
    radio != 'CDMA'
    and mcc between 200 and 799
    and net between 1+1+1+1+1+1+1+1+1+1+1+1+1+1+1 and 999
    and area between smallest_area and biggest_area
    and cell between (select min(cell_number) from numbers) and (
        select max(cell_number) from numbers
    ) and lon between -180 and 180
    or lat between -90 and 90