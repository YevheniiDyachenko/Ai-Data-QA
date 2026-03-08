from ai_data_qa.cli import _load_rules_from_cache


def test_load_rules_from_new_envelope():
    payload = {
        "schema_version": "2.0",
        "rules": [
            {
                "id": "rule_1",
                "table_name": "users",
                "rule_type": "not_null",
                "severity": "high",
                "owner": "data",
                "dimension": "completeness",
                "sql": "SELECT 0 as failed_rows",
                "enabled": True,
                "tags": ["nulls"],
                "metadata": {},
            }
        ],
    }

    rules = _load_rules_from_cache(payload)
    assert len(rules) == 1
    assert rules[0].id == "rule_1"


def test_load_rules_from_legacy_tests_payload():
    payload = {
        "tests": [
            {
                "table_name": "users",
                "test_name": "legacy_test",
                "sql": "SELECT 0 as failed_rows",
                "description": "legacy",
                "tags": ["legacy"],
            }
        ]
    }

    rules = _load_rules_from_cache(payload)
    assert len(rules) == 1
    assert rules[0].id == "legacy_test"
    assert rules[0].metadata["description"] == "legacy"
