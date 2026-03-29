'''
input: read from DB / my_experience.json
output: structured ExperienceItem schema
'''

from __future__ import annotations

import json
from pathlib import Path

from app.config import load_settings
from app.logger import setup_logger
from app.schemas import ExperienceItem

logger = setup_logger(__name__)
settings = load_settings()


def load_experience_db() -> list[ExperienceItem]:
    """
    Load structured experience items from the configured JSON file.
    """
    path = Path(settings.paths.experience_db)
    if not path.exists():
        raise FileNotFoundError(f"Experience DB file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Experience DB path is not a file: {path}")

    raw_data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(raw_data, list):
        raise ValueError("Experience DB must be a JSON list.")

    experiences = [ExperienceItem(**item) for item in raw_data]

    logger.info("Loaded %d experience items from %s", len(experiences), path)

    return experiences

# ----------------------------
# For JD and exp matching 
# ----------------------------
def get_all_experiences() -> list[ExperienceItem]:
    """
    Return all experience items.
    """
    return load_experience_db()


def get_experience_by_id(exp_id: str) -> ExperienceItem | None:
    """
    Retrieve a single experience item by exp_id.
    """
    experiences = load_experience_db()

    for exp in experiences:
        if exp.exp_id == exp_id:
            return exp

    logger.warning("Experience item not found: %s", exp_id)
    return None