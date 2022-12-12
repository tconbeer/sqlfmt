{% call dbt_unit_testing.test('customers', 'should sum order values to calculate customer_lifetime_value') %}
  
  {% call dbt_unit_testing.mock_ref ('stg_customers', {"input_format": "csv"}) %}
    customer_id, first_name, last_name
    1,'',''
  {% endcall %}
  
  {% call dbt_unit_testing.mock_ref ('stg_orders', {"input_format": "csv"}) %}
    order_id,customer_id,order_date
    1001,1,null
    1002,1,null
  {% endcall %}
  
  {% call dbt_unit_testing.mock_ref ('stg_payments', {"input_format": "csv"}) %}
    order_id,amount
    1001,10
    1002,10
  {% endcall %}

  {% call dbt_unit_testing.expect({"input_format": "csv"}) %}
    customer_id,customer_lifetime_value
    1,20
  {% endcall %}
{% endcall %}

{% call dbt_unit_testing.test('customers', 'should sum order values to calculate customer_lifetime_value') %}
  
  {% call dbt_unit_testing.mock_ref ('stg_customers', {"input_format": "csv"}) %}
    customer_id | first_name | last_name
    1           | ''         | ''
  {% endcall %}
  
  {% call dbt_unit_testing.mock_ref ('stg_orders', {"input_format": "csv"}) %}
    order_id | customer_id | order_date 
    1        | 1           | null
    2        | 1           | null
  {% endcall %}
  
  {% call dbt_unit_testing.mock_ref ('stg_payments', {"input_format": "csv"}) %}
    order_id | amount
    1        | 10
    2        | 10
  {% endcall %}

  {% call dbt_unit_testing.expect({"input_format": "csv"}) %}
    customer_id | customer_lifetime_value
    1           | 20
  {% endcall %}
{% endcall %}

{% call dbt_unit_testing.test('customers', 'should show customer_id without orders') %}
  {% call dbt_unit_testing.mock_ref ('stg_customers') %}
    select 1 as customer_id, '' as first_name, '' as last_name
  {% endcall %}

  {% call dbt_unit_testing.mock_ref ('stg_orders') %}
    select null::numeric as customer_id, null::numeric as order_id, null as order_date  
    where false
  {% endcall %}

  {% call dbt_unit_testing.mock_ref ('stg_payments') %}
     select null::numeric as order_id, null::numeric as amount 
     where false
  {% endcall %}
  
  {% call dbt_unit_testing.expect() %}
    select 1 as customer_id
  {% endcall %}
{% endcall %}
)))))__SQLFMT_OUTPUT__(((((
{% call dbt_unit_testing.test(
    "customers",
    "should sum order values to calculate customer_lifetime_value"
) %}

{% call dbt_unit_testing.mock_ref("stg_customers", {"input_format": "csv"}) %}
    customer_id, first_name, last_name
    1,'',''
{% endcall %}

{% call dbt_unit_testing.mock_ref("stg_orders", {"input_format": "csv"}) %}
    order_id,customer_id,order_date
    1001,1,null
    1002,1,null
{% endcall %}

{% call dbt_unit_testing.mock_ref("stg_payments", {"input_format": "csv"}) %}
    order_id,amount
    1001,10
    1002,10
{% endcall %}

{% call dbt_unit_testing.expect({"input_format": "csv"}) %}
    customer_id,customer_lifetime_value
    1,20
{% endcall %}
{% endcall %}

{% call dbt_unit_testing.test(
    "customers",
    "should sum order values to calculate customer_lifetime_value"
) %}

{% call dbt_unit_testing.mock_ref("stg_customers", {"input_format": "csv"}) %}
    customer_id | first_name | last_name
    1           | ''         | ''
{% endcall %}

{% call dbt_unit_testing.mock_ref("stg_orders", {"input_format": "csv"}) %}
    order_id | customer_id | order_date 
    1        | 1           | null
    2        | 1           | null
{% endcall %}

{% call dbt_unit_testing.mock_ref("stg_payments", {"input_format": "csv"}) %}
    order_id | amount
    1        | 10
    2        | 10
{% endcall %}

{% call dbt_unit_testing.expect({"input_format": "csv"}) %}
    customer_id | customer_lifetime_value
    1           | 20
{% endcall %}
{% endcall %}

{% call dbt_unit_testing.test("customers", "should show customer_id without orders") %}
{% call dbt_unit_testing.mock_ref("stg_customers") %}
    select 1 as customer_id, '' as first_name, '' as last_name
{% endcall %}

{% call dbt_unit_testing.mock_ref("stg_orders") %}
    select null::numeric as customer_id, null::numeric as order_id, null as order_date  
    where false
{% endcall %}

{% call dbt_unit_testing.mock_ref("stg_payments") %}
     select null::numeric as order_id, null::numeric as amount 
     where false
{% endcall %}

{% call dbt_unit_testing.expect() %}
    select 1 as customer_id
{% endcall %}
{% endcall %}
