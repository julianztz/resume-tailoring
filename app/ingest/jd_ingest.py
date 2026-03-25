'''
JD 输入处理
将外部输入的JD content转化为统一的JDInput objects

输入          输出
string     -- JDInput
input text -- JDInput
'''

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from app.logger import setup_logger
from app.schemas import JDInput

logger = setup_logger(__name__)


def create_jd_input(
    raw_text: str,
    source: str = "manual_paste",
    job_id: str | None = None,
    company: str | None = None,
    title: str | None = None,
    location: str | None = None,
) -> JDInput:
    """
    Create a JDInput object from raw text and optional metadata.
    """
    cleaned_text = raw_text.strip()

    if not cleaned_text:
        raise ValueError("JD raw_text cannot be empty.")

    jd_input = JDInput(
        source=source,
        job_id=job_id,
        company=company,
        title=title,
        location=location,
        raw_text=cleaned_text,
        captured_at=datetime.now().isoformat(),
    )
    logger.info("Created JDInput from source=%s, title=%s, company=%s", source, title, company)
    return jd_input


def load_jd_from_file(
    file_path: str | Path,
    source: str = "txt_file",
    job_id: str | None = None,
    company: str | None = None,
    title: str | None = None,
    location: str | None = None,
) -> JDInput:
    """
    Load a job description from a text file and convert it into JDInput.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"JD file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    raw_text = path.read_text(encoding="utf-8").strip()

    logger.info("Loaded JD text file: %s", path)

    return create_jd_input(
        raw_text=raw_text,
        source=source,
        job_id=job_id,
        company=company,
        title=title,
        location=location,
    )




