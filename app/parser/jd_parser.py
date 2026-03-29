'''
deterministic extraction： 基本parsing 规则
LLM semantic parsing： LLM mapping 解析

输入：JDInput
输出：JDParsed
'''

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from app.config import load_settings
from app.logger import setup_logger
from app.schemas import JDInput, JDParsed

logger = setup_logger(__name__)
settings = load_settings()

client = OpenAI(api_key=settings.openai_api_key)


# ----------------------------
# Rule-based extraction
# ----------------------------
def extract_basic_fields(text: str) -> dict[str, Any]:
    """
    Extract simple fields like company, title, location using rules.
    """
    result: dict[str, Any] = {}

    # Very naive patterns (can improve later)
    title_match = re.search(r"(?i)(?:job title|position|role):?\s*(.+)", text)
    location_match = re.search(r"(?i)location:?\s*(.+)", text)

    if title_match:
        result["title"] = title_match.group(1).strip()

    if location_match:
        result["location"] = location_match.group(1).strip()

    return result


# keywords dedup & cleanup
def normalize_keywords(keywords: list[str]) -> list[str]:
    seen = set()
    cleaned = []

    for kw in keywords:
        item = kw.strip()
        if not item:
            continue

        key = item.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(item)

    return cleaned

# ----------------------------
# LLM JD parsing -- AI prompt CORE LLM decision
# 判断JD性质
# 返还 JSON {company， title， location， sensiority， skill， signal， summary}
# ----------------------------

'''
generic: basic fields & additional rules
Job specific: signal definitions & important rules
'''
def build_prompt(raw_text: str) -> str:
    return f"""
You are an expert at parsing job descriptions.

Extract structured information from the following job description.

Return a JSON object with the following fields:
- company (string or null)
- title (string or null)
- location (string or null)
- seniority (string or null)
- education (list of strings)
- responsibilities (list of strings)
- required_skills (list of strings)
- preferred_skills (list of strings)
- keywords (list of strings)
- signals (object)
- summary (string)

Addtional rules:
seniorty definitions: Classify the role level based on scope, ownership, and expectations
- junior: Entry-level or early-career roles with close guidance, focused on learning and executing well-defined tasks.
- mid-level: Independent contributors who can deliver features end-to-end with moderate complexity and limited guidance.
- senior: Experienced engineers who own complex systems or features, make design decisions, and may mentor others.
- lead: Engineers who drive technical direction, define strategies, and coordinate across teams or projects.
- staff: Roles with organization-wide impact, setting architecture, standards, and influencing multiple teams or long-term strategy.
required_skills definitions: Include only skills, tools, or knowledge areas explicitly required or clearly stated as must-have / qualifications.
preferred_skills definitions: Include only skills explicitly described as preferred, plus, nice-to-have, or beneficial.
education definitions: Include education information like Bachelor / Master / PhD degrees, new graduates, domain requirement, certifications. 
keywords definitions: Include concise, normalized role-matching terms derived from the JD. Avoid vague soft skills unless they are central to the role.
responsibilities: 4–8 concise bullets
required_skills / preferred_skills: deduplicated concise phrases

Signal definitions:
- customer_facing_internal: true only if the role clearly involves working with internal customers, stakeholders, collaborating with other teams.
- customer_facing_external: true only if the role clearly involves working with customers, external clients, or partner-facing technical communication
- data_heavy: true only if the role strongly emphasizes data processing, metrics, dashboards, reporting, aggregation, or large-scale data analysis.
- analytics_heavy: true only if the role strongly emphasizes analysis, evaluation, insights, trend analysis, explainability, scenario analysis, or performance interpretation.
- applied_ml: true only if the role uses machine learning, LLMs, VLMs, or AI techniques in practical product, evaluation, classification, or workflow applications.
- backend_heavy: true only if the role clearly emphasizes backend services, APIs, distributed systems, microservices, production service ownership, scalability, or infrastructure-heavy backend engineering.
- frontend_heavy: true only if the role clearly emphasizes frontend services, APIs, techniques such as JS, JavaScript, TypeScript, full stack, or frontend engineering.
- research_heavy: true only if the role clearly focuses on model research, algorithm development, experimentation on novel methods, model training/tuning, or research-oriented innovation.
- startup_like: true only if the JD strongly suggests a fast-moving, ambiguous, cross-functional startup environment.
- leadership_heavy: true if the role involves leading initiatives, defining strategy, or coordinating across teams.
- domain_heavy: true if the role requires deep, specialized domain knowledge that cannot be quickly learned.
- system_heavy: true if the role focuses on system-level design, integration, or end-to-end behavior across multiple components.


Important rules:
- Do not infer backend_heavy just because the role is software-related or not frontend.
- Do not infer research_heavy just because the JD mentions AI, LLMs, or VLMs.
- If evidence is weak or ambiguous, set the signal to false.
- Only use information clearly supported by the JD text.
- Normalize obvious variants into a single canonical form when possible.


Job Description:
{raw_text}

Only return valid JSON.
"""


def call_llm_parse(raw_text: str) -> dict[str, Any]:
    """
    Call LLM to parse JD into structured fields.
    """
    response = client.responses.create(
        model=settings.llm.model,
        input=build_prompt(raw_text),
        temperature=settings.llm.temperature,
        max_output_tokens=settings.llm.max_output_tokens,
    )

    # content = response.output[0].content[0].text
    if not response.output_text:
        logger.error("Empty response from LLM")
        raise ValueError("LLM returned empty response")
    content = response.output_text

    # remove markdown code block
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("```json").strip("```").strip()

    try:
        parsed = json.loads(content)                     # ATTENTION -- wrong answer / not json / invalid format
    except json.JSONDecodeError:
        logger.error("Failed to parse LLM response as JSON.")
        logger.error("Raw response: %s", content)
        raise

    return parsed


# ----------------------------
# Main parser function
# ----------------------------

def parse_jd(jd_input: JDInput) -> JDParsed:
    """
    Convert JDInput into JDParsed using hybrid parsing.
    """
    logger.info("Starting JD parsing...")

    # Step 1: rule-based
    basic_fields = extract_basic_fields(jd_input.raw_text)

    # Step 2: LLM parsing
    llm_data = call_llm_parse(jd_input.raw_text)

    # Merge results
    parsed = JDParsed(
        company=jd_input.company or basic_fields.get("company") or llm_data.get("company"),
        title=jd_input.title or basic_fields.get("title") or llm_data.get("title"),
        location=jd_input.location or basic_fields.get("location") or llm_data.get("location"),
        seniority=llm_data.get("seniority"),
        responsibilities=llm_data.get("responsibilities", []),
        required_skills=llm_data.get("required_skills", []),
        preferred_skills=llm_data.get("preferred_skills", []),
        keywords=normalize_keywords(llm_data.get("keywords", [])),
        signals=llm_data.get("signals", {}),
        summary=llm_data.get("summary", ""),
    )

    logger.info("JD parsing completed.")

    return parsed



   