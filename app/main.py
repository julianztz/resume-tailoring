from __future__ import annotations

import typer
from rich import print

from app.config import load_settings
from app.schemas import ExperienceItem, JDInput
from app.logger import setup_logger

app = typer.Typer(help="Resume tailoring project CLI")       # CLI 对象 ie. python -m app.main health

@app.command("schema-test")
def schema_test():
    jd = JDInput(
        company="OpenAI",
        title="AI Engineer",
        raw_text="Build production AI systems using Python and APIs."
    )

    exp = ExperienceItem(
        exp_id="exp_001",
        project="Display Validation Platform",
        role="Software Developer",
        skills=["Python", "automation", "data analysis"],
        bullets=["Built Python tools for workflow automation."]
    )

    print(jd.model_dump())
    print(exp.model_dump())

@app.command("logger-test")
def logger_test():
    settings = load_settings()
    print("Resume generating...")
    print(settings)
    logger = setup_logger(__name__)
    logger.info("Project started successfully.")
    logger.info("Loaded project: %s", settings.project_name)
    logger.info("Using model: %s", settings.llm.model)

@app.command()
def health() -> None:
    """
    Basic health check for the project.
    Verifies that config loading and logger setup work.
    """
    logger = setup_logger(__name__)
    settings = load_settings()

    logger.info("Health check started.")
    logger.info("Project name: %s", settings.project_name)
    logger.info("LLM provider: %s", settings.llm.provider)
    logger.info("LLM model: %s", settings.llm.model)

    print("[green]Project health check passed.[/green]")
    print(f"[cyan]Project:[/cyan] {settings.project_name}")
    print(f"[cyan]Provider:[/cyan] {settings.llm.provider}")
    print(f"[cyan]Model:[/cyan] {settings.llm.model}")


def main() -> None:
    app()

'''
CLI -- application entry point 系统入口

--不关心实现细节--
'''
if __name__ == "__main__":
    main()