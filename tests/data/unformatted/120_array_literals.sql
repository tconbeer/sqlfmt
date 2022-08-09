select
    'xero' as billing_platform, [invoice_id, invoice.invoice_number] as billing_platform_references,
from hello
;
select
    split_array('foo, bar, baz, qux', ',')[2] as baz, ['foo', 'bar', 'baz', 'qux'] as literal, ['foo', 'bar', 'baz', 'qux'][2] as indexed_literal,
    some_table.some_dict['a key'] as dict_access
from bar
)))))__SQLFMT_OUTPUT__(((((
select
    'xero' as billing_platform,
    [invoice_id, invoice.invoice_number] as billing_platform_references,
from hello
;
select
    split_array('foo, bar, baz, qux', ',')[2] as baz,
    ['foo', 'bar', 'baz', 'qux'] as literal,
    ['foo', 'bar', 'baz', 'qux'][2] as indexed_literal,
    some_table.some_dict['a key'] as dict_access
from bar
