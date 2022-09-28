select *
from (values 
    (1, 2, 3),
    (4, 5, 6)
);
select *
from (values ('some long string literal', 'another very long literal', 'more string literal values', 1, 2, 3),
    ('some long string literal', 'another very long literal', 'more string literal values', 4, 5, 6),
            ('something shorter', 'short', 'fits', 7, 8, 9)
) as v;
)))))__SQLFMT_OUTPUT__(((((
select *
from (values (1, 2, 3), (4, 5, 6))
;
select *
from
    (
        values
            (
                'some long string literal',
                'another very long literal',
                'more string literal values',
                1,
                2,
                3
            ),
            (
                'some long string literal',
                'another very long literal',
                'more string literal values',
                4,
                5,
                6
            ),
            ('something shorter', 'short', 'fits', 7, 8, 9)
    ) as v
;
