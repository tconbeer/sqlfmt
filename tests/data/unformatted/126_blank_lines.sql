
{{ config(foo='bar') }}



select


foooooooooooo,
barrrrrrrrrrr,


bazzzzzzzzzzz,

quxxxxxxxxxxx,


foooooooooooo + barrrrrrrrrr + bazzzzzzzzzzz + quxxxxxxxxxxx as foooooooooooo_bar_baz_qux
from
fooooooooooooo.barrrrrrrrrr.bazzzzzzzzzzzzzz

where


quxxxxxxxxxxx=1
{% if is_incremental() %}


and barrrrrrrrrr = 1





and bazzzzzzzzzzz = 2
and quxxxxxxxxxxx = 3




{% endif %}
;






select 1
)))))__SQLFMT_OUTPUT__(((((
{{ config(foo="bar") }}


select

    foooooooooooo,
    barrrrrrrrrrr,

    bazzzzzzzzzzz,

    quxxxxxxxxxxx,

    foooooooooooo
    + barrrrrrrrrr
    + bazzzzzzzzzzz
    + quxxxxxxxxxxx as foooooooooooo_bar_baz_qux
from fooooooooooooo.barrrrrrrrrr.bazzzzzzzzzzzzzz

where

    quxxxxxxxxxxx = 1
    {% if is_incremental() %}

        and barrrrrrrrrr = 1 and bazzzzzzzzzzz = 2 and quxxxxxxxxxxx = 3

    {% endif %}
;


select 1
