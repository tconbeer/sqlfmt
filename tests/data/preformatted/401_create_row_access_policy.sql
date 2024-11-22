create or replace row access policy foo
on foo.bar.baz
grant to ('user1', 'user2')
filter using ( foo = 'bar' )
