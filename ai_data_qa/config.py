import yaml
import os
from pydantic import BaseModel, Field
from typing import List, Optional

class AIConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    api_key_env_var: str = "OPENAI_API_KEY"

class TestsConfig(BaseModel):
    output_dir: str = "tests_generated"
    default_checks: List[str] = ["not_null", "uniqueness"]

class ReportConfig(BaseModel):
    output_dir: str = "reports"

class Config(BaseModel):
    project_id: str
    dataset: str
    location: str = "US"
    ai: AIConfig
    tests: TestsConfig
    report: ReportConfig

def load_config(path: str = "config.yaml") -> Config:
    """Loads configuration from a YAML file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return Config(**data)
