'''
infrastructure / 统一数据格式 (object)
 -- 定义data structure model
 -- 利用Pydantic 约束数据格式契约（schema）
 -- 在每一层模块传递数据时确保数据的统一格式类型
 
统一定义输入输出对象
让各模块之间的数据边界清晰
减少后面到处传 dict 的混乱

--不关心逻辑--
'''

from __future__ import annotations
from nt import system
from typing import Literal
from pydantic import BaseModel, Field     # 类型注解（type hints）的 数据/解析/建模 库

'''
原始JD输入： ie. copy from job posting
'''
class JDInput(BaseModel):
    source: str = "manual_paste"
    job_id: str | None = None
    company: str | None = None
    title: str | None = None
    location: str | None = None
    raw_text: str
    captured_at: str | None = None

'''
JD中提取的高级信号；for etendability
'''
class JDSignals(BaseModel):
    customer_facing_internal: bool = False
    customer_facing_external: bool = False
    data_heavy: bool = False
    analytics_heavy: bool = False
    applied_ml: bool = False
    backend_heavy: bool = False
    frontend_heavy: bool = False
    research_heavy: bool = False
    startup_like: bool = False
    leadership_heavy: bool = False
    domain_heavy: bool = False
    system_heavy: bool = False
    

'''
结构化JD输出结果
'''
class JDParsed(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    seniority: str | None = None
    education: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    signals: JDSignals = Field(default_factory=JDSignals)
    summary: str = ""


'''
my experience 
每段个人经验包装成一个ExperienceItem
'''
class ExperienceItem(BaseModel):
    exp_id: str
    company: str | None = None
    project: str
    role: str
    period: str | None = None

    skills: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    strength_tags: list[str] = Field(default_factory=list)            # signal layer 
    core_capabilities: list[str] = Field(default_factory=list)        # match layer -- output to match result

    bullets: list[str] = Field(default_factory=list)                  # detail layer -- source
    impact_summary: str | None = None


'''
JD 与my exp之间的匹配分析结果
'''
class MatchResult(BaseModel):
    overall_score: int = 0
    skill_match_score: int = 0
    responsibility_match_score: int = 0
    domain_match_score: int = 0
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    top_experience_ids: list[str] = Field(default_factory=list)
    experience_scores: list[ExperienceMatchScore] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    narrative: str = ""
    

'''
每条experience的matching score
'''
class ExperienceMatchScore(BaseModel):
    exp_id: str
    score: int = 0
    matched_skills: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    matched_signals: list[str] = Field(default_factory=list)
    rationale: str = ""

'''
decision gate / 建议生成器
根据MatchResult结果提出建议，是否继续申请
'''
class ApplyRecommendation(BaseModel):
    recommend_apply: bool = False
    confidence: float = 0.0
    reason_summary: str = ""
    user_action_needed: Literal["confirm_apply", "skip", "review"] = "review"


'''
这是 tailoring 模块的输出 -- 定制后的简历草稿
'''
class TailoredResumeDraft(BaseModel):
    target_company: str | None = None
    target_title: str | None = None
    selected_experience_ids: list[str] = Field(default_factory=list)
    tailored_summary: str = ""
    tailored_bullets: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)