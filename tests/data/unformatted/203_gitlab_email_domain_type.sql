# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE: https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE

{% macro email_domain_type(email_domain, lead_source) %}

{%- set personal_email_domains_partial_match = get_personal_email_domain_list('partial_match') -%}
{%- set personal_email_domains_full_match = get_personal_email_domain_list('full_match') -%}


CASE
  WHEN {{lead_source}} IN ('DiscoverOrg', 'Zoominfo', 'Purchased List', 'GitLab.com') THEN 'Bulk load or list purchase or spam impacted'
  WHEN TRIM({{email_domain}}) IS NULL THEN 'Missing email domain'

  WHEN {{email_domain}} LIKE ANY (
    {%- for personal_email_domain in personal_email_domains_partial_match -%}
    '%{{personal_email_domain}}%' {%- if not loop.last -%}, {% endif %}
    {% endfor %}
  )

  OR {{email_domain}} IN (
    {%- for personal_email_domain in personal_email_domains_full_match -%}
    '{{personal_email_domain}}' {%- if not loop.last -%}, {% endif %}
    {% endfor %}
  )

  OR NOT {{email_domain}} NOT IN (
    {%- for personal_email_domain in personal_email_domains_full_match -%}
    '{{personal_email_domain}}' {%- if not loop.last -%}, {% endif %}
    {% endfor %}
  )

  THEN 'Personal email domain'
  ELSE 'Business email domain'
END

{% endmacro %}
)))))__SQLFMT_OUTPUT__(((((
# COPYRIGHT GITLAB, USED UNDER MIT LICENSE
# SEE:
# https://github.com/tconbeer/gitlab-analytics-sqlfmt/blob/9360d2f1986c37615926b0416e8d0fb23cae3e6e/LICENSE
{% macro email_domain_type(email_domain, lead_source) %}

    {%- set personal_email_domains_partial_match = get_personal_email_domain_list(
        "partial_match"
    ) -%}
    {%- set personal_email_domains_full_match = get_personal_email_domain_list(
        "full_match"
    ) -%}

    case
        when
            {{ lead_source }}
            in ('DiscoverOrg', 'Zoominfo', 'Purchased List', 'GitLab.com')
        then 'Bulk load or list purchase or spam impacted'
        when trim({{ email_domain }}) is null
        then 'Missing email domain'

        when
            {{ email_domain }} like any (
                {%- for personal_email_domain in personal_email_domains_partial_match -%}
                    '%{{personal_email_domain}}%' {%- if not loop.last -%}, {% endif %}
                {% endfor %}
            )

            or {{ email_domain }} in (
                {%- for personal_email_domain in personal_email_domains_full_match -%}
                    '{{personal_email_domain}}' {%- if not loop.last -%}, {% endif %}
                {% endfor %}
            )

            or not {{ email_domain }} not in (
                {%- for personal_email_domain in personal_email_domains_full_match -%}
                    '{{personal_email_domain}}' {%- if not loop.last -%}, {% endif %}
                {% endfor %}
            )

        then 'Personal email domain'
        else 'Business email domain'
    end

{% endmacro %}
