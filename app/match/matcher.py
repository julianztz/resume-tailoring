"""
JD & experience matching logic

1. skill overlap -- 显式经验比较
JD.required_skills      vs     Experience.skills
JD.preferred_skills     vs     Experience.tools


2. keyword / capability overlap -- keywords 比较
JD.keywords
       vs 
Experience.core_capabilities
Experience.domains
Experience.strength_tags

3. signal-based boosting -- 根据 JD signals，给某些 experience tag 加分。
eg.
backend_heavy=True → boost backend_systems
applied_ml=True → boost ai_application
data_heavy=True → boost data_processing
analytics_heavy=True → boost data_processing, tooling
customer_facing=True → 以后可 boost stakeholder-facing exp

4. top experience ranking -- 每条经验算总分，排序后选 top N

"""

from __future__ import annotations

from typing import Iterable

from app.logger import setup_logger
from app.schemas import (
    ExperienceItem,
    ExperienceMatchScore,
    JDParsed,
    MatchResult,
)

logger = setup_logger(__name__)


TAG_BOOST_RULES = {
    "backend_heavy": {"backend_systems": 3, "api_design": 2, "system_design": 2},
    "applied_ml": {"ai_application": 3, "modular_architecture": 2, "system_design": 1},
    "data_heavy": {"data_processing": 3, "automation": 1, "tooling": 1},
    "analytics_heavy": {"data_processing": 2, "tooling": 2},
    "research_heavy": {"research": 3},
    "customer_facing": {"customer_facing": 2},
    "startup_like": {"ownership": 2, "modular_architecture": 1},
}


def normalize_text_list(items: Iterable[str]) -> set[str]:
    """
    Normalize a list of strings into a lowercase stripped set.
    """
    return {
        item.strip().lower()
        for item in items
        if isinstance(item, str) and item.strip()
    }

'''
explict skill matching
'''
def compute_skill_overlap(jd: JDParsed, exp: ExperienceItem) -> tuple[int, list[str], list[str]]:
    """
    Compare JD skills against experience skills and tools.
    """
    jd_required = normalize_text_list(jd.required_skills)
    jd_preferred = normalize_text_list(jd.preferred_skills)

    exp_skills = normalize_text_list(exp.skills)
    exp_tools = normalize_text_list(exp.tools)

    exp_pool = exp_skills | exp_tools

    matched_required = sorted(jd_required & exp_pool)
    matched_preferred = sorted(jd_preferred & exp_pool)

    score = len(matched_required) * 4 + len(matched_preferred) * 2

    return score, matched_required, matched_preferred

'''
keyword based matching
'''
def compute_keyword_overlap(jd: JDParsed, exp: ExperienceItem) -> tuple[int, list[str]]:
    """
    Compare JD keywords against experience domains, capabilities, and strength tags.
    """
    jd_keywords = normalize_text_list(jd.keywords)

    exp_domains = normalize_text_list(exp.domains)
    exp_capabilities = normalize_text_list(getattr(exp, "core_capabilities", []))
    exp_tags = normalize_text_list(exp.strength_tags)

    exp_pool = exp_domains | exp_capabilities | exp_tags

    matched_keywords = sorted(jd_keywords & exp_pool)
    score = len(matched_keywords) * 3

    return score, matched_keywords

'''
adding extra weights according to the signals
'''
def compute_signal_boost(jd: JDParsed, exp: ExperienceItem) -> tuple[int, list[str]]:
    """
    Add boost scores based on JD signals and experience strength tags.
    """
    exp_tags = normalize_text_list(exp.strength_tags)

    boost_score = 0
    matched_signals: list[str] = []

    signal_map = jd.signals.model_dump()

    for signal_name, is_enabled in signal_map.items():
        if not is_enabled:
            continue

        tag_rules = TAG_BOOST_RULES.get(signal_name, {})
        for tag, points in tag_rules.items():
            if tag in exp_tags:
                boost_score += points
                matched_signals.append(f"{signal_name}:{tag}")

    return boost_score, matched_signals

'''
scoring each experience
'''
def score_experience(jd: JDParsed, exp: ExperienceItem) -> ExperienceMatchScore:
    """
    Score a single experience item against the JD.
    """
    skill_score, matched_required, matched_preferred = compute_skill_overlap(jd, exp)
    keyword_score, matched_keywords = compute_keyword_overlap(jd, exp)
    signal_score, matched_signals = compute_signal_boost(jd, exp)

    total_score = skill_score + keyword_score + signal_score

    rationale_parts = []
    if matched_required:
        rationale_parts.append(f"required skills matched: {', '.join(matched_required)}")
    if matched_preferred:
        rationale_parts.append(f"preferred skills matched: {', '.join(matched_preferred)}")
    if matched_keywords:
        rationale_parts.append(f"keywords matched: {', '.join(matched_keywords)}")
    if matched_signals:
        rationale_parts.append(f"signal boosts: {', '.join(matched_signals)}")

    rationale = "; ".join(rationale_parts) if rationale_parts else "limited direct overlap"

    return ExperienceMatchScore(
        exp_id=exp.exp_id,
        score=total_score,
        matched_skills=matched_required + matched_preferred,
        matched_keywords=matched_keywords,
        matched_signals=matched_signals,
        rationale=rationale,
    )

'''
return top N matching experience with scores
'''
def build_match_result(jd: JDParsed, experiences: list[ExperienceItem], top_k: int = 4) -> MatchResult:
    """
    Score all experiences and build an overall MatchResult.
    """
    logger.info("Starting JD-to-experience matching with %d experiences", len(experiences))

    experience_scores = [score_experience(jd, exp) for exp in experiences]
    experience_scores.sort(key=lambda x: x.score, reverse=True)

    top_scores = experience_scores[:top_k]
    top_ids = [item.exp_id for item in top_scores]

    all_matched_skills = sorted({
        skill
        for item in top_scores
        for skill in item.matched_skills
    })

    jd_required = normalize_text_list(jd.required_skills)
    matched_skill_set = set(all_matched_skills)
    missing_skills = sorted(jd_required - matched_skill_set)

    # simple aggregate scoring
    skill_match_score = min(len(all_matched_skills) * 10, 100)
    domain_match_score = min(sum(item.score for item in top_scores), 100)
    responsibility_match_score = 0  # placeholder for next version

    overall_score = int((skill_match_score * 0.45) + (domain_match_score * 0.35) + (responsibility_match_score * 0.20))

    strengths = []
    risks = []

    if all_matched_skills:
        strengths.append(f"Strong overlap in: {', '.join(all_matched_skills[:6])}")

    if top_ids:
        strengths.append(f"Most relevant experiences: {', '.join(top_ids)}")

    if missing_skills:
        risks.append(f"Potential gaps: {', '.join(missing_skills[:6])}")

    narrative = (
        f"Top matched experiences are {', '.join(top_ids)}. "
        f"The profile shows strongest overlap in {', '.join(all_matched_skills[:5]) if all_matched_skills else 'limited directly matched skills'}."
    )

    logger.info("Matching complete. Top experiences: %s", top_ids)

    return MatchResult(
        overall_score=overall_score,
        skill_match_score=skill_match_score,
        responsibility_match_score=responsibility_match_score,
        domain_match_score=domain_match_score,
        matched_skills=all_matched_skills,
        missing_skills=missing_skills,
        top_experience_ids=top_ids,
        experience_scores=top_scores,
        strengths=strengths,
        risks=risks,
        narrative=narrative,
    )