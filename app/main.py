from __future__ import annotations

import typer
from rich import print
from openai import OpenAI

from app.config import load_settings
from app.parser.jd_parser import parse_jd
from app.schemas import ExperienceItem, JDInput
from app.logger import setup_logger
from app.ingest.jd_ingest import load_jd_from_file
from app.store.experience_store import get_all_experiences

app = typer.Typer(help="Resume tailoring project CLI")       # CLI 对象 ie. python -m app.main health

# ----------------------------
# test for schema
# ----------------------------
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

# ----------------------------
# test for logger
# ----------------------------
@app.command("logger-test")
def logger_test():
    settings = load_settings()
    print("Resume generating...")
    print(settings)
    logger = setup_logger(__name__)
    logger.info("Project started successfully.")
    logger.info("Loaded project: %s", settings.project_name)
    logger.info("Using model: %s", settings.llm.model)


# ----------------------------
# test project settings
# ----------------------------
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


# ----------------------------
# test LLM & api key settings
# ----------------------------
@app.command()
def test_llm() -> None:
    logger = setup_logger(__name__)
    settings = load_settings()

    client = OpenAI(api_key=settings.openai_api_key)

    response = client.responses.create(
        model=settings.llm.model,
        input="Say hello in one sentence.",
    )

    # text = response.output[0].content[0].text
    if not response.output_text:
        logger.error("Empty response from LLM")
        raise ValueError("LLM returned empty response")

    content = response.output_text

    logger.info("LLM test response received.")
    print("[green]LLM test success[/green]")
    print(content)


# ----------------------------
# testing jd_ingest
# input normalization pipeline
# CLI -> ingest -> schema(object)
# ----------------------------
@app.command()
def ingest_jd_cmd(file_path: str) -> None:
    """
    Load a JD text file and print the structured JDInput.
    """
    logger = setup_logger(__name__)
    jd_input = load_jd_from_file(file_path)

    logger.info("JD ingest command completed successfully.")
    print("[green]JD ingest succeeded.[/green]")
    print(jd_input.model_dump())



@app.command()
def parse_jd_cmd(file_path: str) -> None:
    """
    load JD text file -> JDInput
    parse JDInput -> JDParsed
          basic rule
          LLM prompt
    """
    logger = setup_logger(__name__)
    settings = load_settings()
    jd_input = load_jd_from_file(file_path)
    jd_parsed = parse_jd(jd_input)

    logger.info("JD parse command completed successfully.")
    logger.info("API key loaded: %s", bool(settings.openai_api_key))
    print("[green]JD parsing succeeded.[/green]")
    print(jd_parsed.model_dump())


@app.command()
def load_experience() -> None:
    logger = setup_logger(__name__)
    settings = load_settings()
    experiences = get_all_experiences()

    logger.info("Experience load command completed.")
    logger.info("Experience DB path: %s", settings.paths.experience_db)
    print("[green]Experience DB loaded successfully.[/green]")
    print([exp.model_dump() for exp in experiences])




def main() -> None:
    app()

'''
CLI -- application entry layer 应用/系统入口

--不关心实现细节，只负责调度--
接受CLI （argument）
调用其他模块
输出结果
'''
if __name__ == "__main__":
    main()