TEST_GENERATION_PROMPT = """
You are a data quality engineer.

Given the following table schema and profiling statistics:

Table: {table_name}
Schema:
{schema_desc}

Profiling Stats:
{profiling_desc}

Generate additional SQL data quality tests for BigQuery.
Focus on:
- format validation
- timestamp sanity checks
- business logic constraints

Return ONLY valid JSON with this schema:
{{
  "tests": [
    {{
      "test_name": "string",
      "sql": "SELECT ...",
      "description": "string",
      "tags": ["freshness" | "nulls" | "distribution"]
    }}
  ]
}}
Each SQL query must return a column named 'failed_rows' representing the count of failed rows.
"""

FAILURE_ANALYSIS_PROMPT = """
You are a data quality analyst.

A data quality test failed.

Table: {table_name}
Test: {test_name}
Failed Rows: {failed_rows}
SQL: {sql}

Schema:
{schema_desc}

Analyze possible root causes and suggest investigation steps.
Provide your response in two parts:
1. Findings: A summary of why this might be happening.
2. Suggested Investigation: SQL queries or steps to further investigate.

Format the output clearly.
"""
