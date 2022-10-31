SELECT ARRAY<FLOAT64>[1, 2, 3] as floats,
STRUCT("Nathan" as name, ARRAY<FLOAT64>[] as laps),
STRUCT<INT32, INT64>(1, 2),
array<INT64>[3, 4, 5, 6, 1000000, 20000000, 30000000, 409000000, 5000000, 60000000, 700000] as ints,
array<string>['1', '2', '3'] as strings;
create function foo(bar struct<string, array<bytes(5)>, int64>)
returns struct<
string, 
array<
bytes(
    5
    )>, int64>
as bar
)))))__SQLFMT_OUTPUT__(((((
select
    array<float64>[1, 2, 3] as floats,
    struct("Nathan" as name, array<float64>[] as laps),
    struct<int32, int64>(1, 2),
    array<int64>[
        3, 4, 5, 6, 1000000, 20000000, 30000000, 409000000, 5000000, 60000000, 700000
    ] as ints,
    array<string>['1', '2', '3'] as strings
;
create function foo(bar struct<string, array<bytes(5)>, int64>)
returns struct<string, array<bytes(5)>, int64>
as bar
