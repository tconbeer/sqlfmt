create database mytestdb_clone clone mytestdb;
create schema mytestschema_clone_restore clone testschema before (timestamp => to_timestamp(40*365*86400));
create table orders_clone_restore clone orders at (timestamp => to_timestamp_tz('04/05/2013 01:02:03', 'mm/dd/yyyy hh24:mi:ss'));
CREATE TABLE ORDERS_CLONE_RESTORE clone orders before (statement => '8e5d0ca9-005e-44e6-b858-a8f5b37c5726');
)))))__SQLFMT_OUTPUT__(((((
create database mytestdb_clone
clone mytestdb
;
create schema mytestschema_clone_restore
clone testschema before (timestamp => to_timestamp(40 * 365 * 86400))
;
create table orders_clone_restore
clone
    orders
    at (timestamp => to_timestamp_tz('04/05/2013 01:02:03', 'mm/dd/yyyy hh24:mi:ss'))
;
create table orders_clone_restore
clone orders before (statement => '8e5d0ca9-005e-44e6-b858-a8f5b37c5726')
;
