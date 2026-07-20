{#
  Write models into the exact schema named in +schema (staging / marts),
  instead of dbt's default "<target>_<custom>" concatenation. Keeps the
  warehouse layout aligned with the raw/staging/marts layers.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
