{% macro test(key) %}
    {% set columns_by_source = {
        "a": """
        column_a1,
        column_a2,
        column_a3,
        """,
        "b": """
        column_b1,
        column_b2,
        """,
        "c": (
            "foooooooooooooooooooo,\n"
            "barrrrrrrrrrrrrrrrrrr,\n"
            "bazzzzzzzzzzzzzzzzzzz,\n"
        ),
    } %}
{% endmacro %}
