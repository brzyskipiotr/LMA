from pydantic import BaseModel
from datetime import datetime


class Evidence(BaseModel):
    page_no: int
    snippet: str


class ExtractedFact(BaseModel):
    field: str
    value: str | float | int | None = None
    unit: str | None = None
    confidence: float
    evidence: list[Evidence] = []


class VerificationResult(BaseModel):
    check_id: str
    check_type: str
    inputs: dict
    result: str  # OK, MARGINAL, OUTLIER
    delta_pct: float | None = None
    why: str
    pages_to_verify: list[int] = []


class RedFlag(BaseModel):
    flag_id: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    category: str
    title: str
    description: str
    pages_to_verify: list[int] = []
    recommended_action: str


class ScoreCard(BaseModel):
    evidence_coverage: int
    consistency: int
    feasibility: int
    traffic_light: str  # GREEN, YELLOW, RED
    pages_to_verify: list[int] = []
    missing_data: list[str] = []


class PageInfo(BaseModel):
    page_no: int
    has_text: bool
    char_count: int


class DocumentMeta(BaseModel):
    doc_id: str
    filename: str
    sha256: str
    pages: int
    created_at: datetime


class AnalysisReport(BaseModel):
    document: DocumentMeta
    page_info: list[PageInfo]
    facts: list[ExtractedFact]
    verifications: list[VerificationResult]
    red_flags: list[RedFlag]
    scorecard: ScoreCard
