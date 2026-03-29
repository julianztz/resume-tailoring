'''
核心配置文件 供其他模块读取config
其他模块避免从.env settings.yaml读取配置

--不关心业务--
'''

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Project root:
# app/config.py -> parent is app/, parent.parent is project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
SETTINGS_PATH = BASE_DIR / "config" / "settings.yaml"


class ScoringConfig(BaseModel):
    apply_threshold: int = 75
    strong_apply_threshold: int = 85


class PathsConfig(BaseModel):
    experience_db: str = "data/my_experience/experience_db.json"
    input_dir: str = "data/inputs"
    output_dir: str = "data/outputs"


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-5"
    temperature: float = 0.2
    max_output_tokens: int = 2000


class AppConfig(BaseModel):
    project_name: str = "resume_tailoring"
    openai_api_key: str | None = None
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

# 读取settings.yaml 配置文件
def _load_yaml_file(path: Path) -> dict[str, Any]:
    """Load YAML file into a dict. Return empty dict if file does not exist."""
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"YAML config must be a dictionary at top level: {path}")

    return data


def load_settings() -> AppConfig:
    """
    Load configuration from:
    1. .env
    2. config/settings.yaml

    Environment variables can override parts of YAML config.
    """
    load_dotenv(ENV_PATH)

    yaml_data = _load_yaml_file(SETTINGS_PATH)

    llm_yaml = yaml_data.get("llm", {}) if isinstance(yaml_data.get("llm", {}), dict) else {}
    scoring_yaml = yaml_data.get("scoring", {}) if isinstance(yaml_data.get("scoring", {}), dict) else {}
    paths_yaml = yaml_data.get("paths", {}) if isinstance(yaml_data.get("paths", {}), dict) else {}

    config = AppConfig(
        project_name=yaml_data.get("project_name", "resume_tailoring"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        scoring=ScoringConfig(
            apply_threshold=scoring_yaml.get("apply_threshold", 75),
            strong_apply_threshold=scoring_yaml.get("strong_apply_threshold", 85),
        ),
        paths=PathsConfig(
            experience_db=paths_yaml.get("experience_db", "data/my_experience/experience_db.json"),
            input_dir=paths_yaml.get("input_dir", "data/inputs"),
            output_dir=paths_yaml.get("output_dir", "data/outputs"),
        ),
        llm=LLMConfig(
            provider=os.getenv("LLM_PROVIDER", llm_yaml.get("provider", "openai")),
            model=os.getenv("OPENAI_MODEL", llm_yaml.get("model", "gpt-5")),
            temperature=llm_yaml.get("temperature", 0.2),
            max_output_tokens=llm_yaml.get("max_output_tokens", 2000),
        ),
    )

    return config