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

Return ONLY the SQL queries, one per line or separated by double newlines.
Each query must return a column named 'failed_rows' representing the count of rows that failed the test.
Example:
SELECT COUNT(*) as failed_rows FROM table WHERE price < 0
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
