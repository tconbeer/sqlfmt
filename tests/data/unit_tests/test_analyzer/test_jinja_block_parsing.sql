{% macro conditionally_loop(contents, num_times) %}
    {% if contents == "foo" %}
        {%- for _ in range(num_times * 10) %}
            {{ contents }}
        {% endfor %}
    {% elif contents == "bar" %}
        {% if num_times > 10 %}
            {%- for _ in range(num_times * 5) %}
                "TIMES 5!!"
                {{ contents }}
            {% endfor %}
        {% else %}
            {%- for _ in range(num_times * 2) %}
                {{ contents }}
            {% endfor %}
        {% endif %}
    {% else %}
        {%- for _ in range(num_times) %}
            {{ contents }}
        {% endfor %}
    {% endif %}
{% endmacro %}