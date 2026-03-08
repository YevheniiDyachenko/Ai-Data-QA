from ai_data_qa.config import load_config


def test_load_config_contains_checks():
    cfg = load_config("config.yaml")
    assert cfg.checks.accepted_values.enabled is True
    assert cfg.checks.freshness_sla.threshold == 24
