SELECT t.customer_sk AS `Customer_IdDWH`, t.customer_id AS `Customer_IdOrig`, t.__identity AS `CustomerCreditLimit_Agg_IdDWH`, t.kreditlimit_intern /* not existing, proposal: credit_limit_intern (92%) */ AS `KreditlimitIntern`, t.kreditlimit_versichert /* not existing */ AS `KreditlimitVersichert`, t.valid_from /* not existing */ AS `ValidFrom`, t.valid_to /* not existing */ AS `ValidTo` FROM `gold`.`dim_customer_credit_limit_agg` AS t
)))))__SQLFMT_OUTPUT__(((((
select
    t.customer_sk as `Customer_IdDWH`,
    t.customer_id as `Customer_IdOrig`,
    t.__identity as `CustomerCreditLimit_Agg_IdDWH`,
    t.kreditlimit_intern  /* not existing, proposal: credit_limit_intern (92%) */
    as `KreditlimitIntern`,
    t.kreditlimit_versichert  /* not existing */
    as `KreditlimitVersichert`,
    t.valid_from  /* not existing */
    as `ValidFrom`,
    t.valid_to  /* not existing */
    as `ValidTo`
from `gold`.`dim_customer_credit_limit_agg` as t
