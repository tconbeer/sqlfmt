-- fmt: off
with abc as (
    select
        *
		{% if env_var('X') == 'Y' %}

		        ,dense_rank() over(partition by z order by y desc) as foo
		{% endif %}

    from {{ ref('stg_something')}}

),

abc as (
    select * from
    country_trial
    {% if env_var('X') == 'Y' %}

		where foo = 1
	{% endif %}

)

select * from dim_something
