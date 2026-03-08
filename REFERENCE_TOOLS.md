Reference Tools and Architectural Inspiration

This project is inspired by several existing open-source data quality and data observability tools.
The goal is not to replicate these systems, but to adopt proven design patterns while adding AI-assisted capabilities.

Below are the main tools used as references and the specific concepts adopted from each.

---

1. Great Expectations

Reference:

https://github.com/great-expectations/great_expectations

Great Expectations is one of the most widely used data quality frameworks.

Core idea:
Data quality rules are defined as Expectations.

Example expectation:

column values must not be null
column values must be unique

Concepts to adopt

Expectation-style validation rules:

- not_null
- uniqueness
- value ranges
- regex patterns

Human-readable reporting.

Example:

Expectation: column user_id must be unique
Result: FAILED
Unexpected values: 135

Clear documentation of data assumptions.

What we intentionally do NOT copy

- heavy configuration system
- complex project scaffolding
- large dependency footprint

This project focuses on a lightweight approach.

---

2. Soda Core

Reference:

https://github.com/sodadata/soda-core

Soda Core provides SQL-based data quality testing.

Example rule syntax:

checks for users:
  - row_count > 0
  - duplicate_count(user_id) = 0

Concepts to adopt

SQL-first testing.

All checks should ultimately compile to SQL queries executed directly in BigQuery.

This keeps the system simple and transparent.

Example:

SELECT COUNT(*)
FROM users
WHERE user_id IS NULL

Advantages:

- easy debugging
- warehouse-native execution
- scalable queries

---

3. dbt Tests

Reference:

https://github.com/dbt-labs/dbt-core

dbt introduced a very successful model for data tests.

Example test types:

- not_null
- unique
- accepted_values
- relationships

Concepts to adopt

Reusable test templates.

Example:

not_null(column)
unique(column)

These should internally compile to SQL queries.

This project will generate such tests automatically using AI.

---

4. Data Observability Platforms

Reference systems include:

- Monte Carlo
- Datafold
- Bigeye

These are commercial platforms and are not open source.

However, they provide useful design ideas.

Concepts to adopt

Quality scoring.

Each table receives a score:

quality_score = passed_tests / total_tests

Example:

users table
tests: 12
passed: 10
score: 83%

Trend monitoring.

Quality should be evaluated over time.

---

5. Key Differentiator of This Project

Existing tools primarily focus on static validation rules.

This project introduces AI-assisted data quality workflows.

AI will be used for:

- automatic test generation from schema
- anomaly analysis
- root cause investigation
- automated documentation

Example workflow:

test failure detected
→ AI generates investigation queries
→ queries executed in BigQuery
→ AI analyzes results
→ possible root cause suggested

Example output:

Test failure: duplicate_user_id

AI investigation result:

Duplicates originate primarily from source_system = legacy_api.

Possible cause:
event ingestion retry mechanism.

This significantly reduces the time required for data incident investigation.

---

Design Philosophy

The project follows several guiding principles:

1. Keep the system simple
2. Prefer SQL-based validation
3. Avoid heavy frameworks
4. Focus on developer experience
5. Use AI to reduce manual work

The first version should remain lightweight and easy to maintain for a single engineer.
