"""
Response Schemas for Darukaa.Earth
===================================
Provides typed, validated API response models for chat turns and standalone reports.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.recommendations.generator import Recommendation


class MetricSummary(BaseModel):
    field_name: str
    value: Any
    unit: Optional[str] = None
    status: str
    confidence: Optional[float] = None
    source_notes: Optional[str] = None


class ProfileSummaryResponse(BaseModel):
    region_name: Optional[str] = None
    biome: Optional[str] = None
    known_metrics: List[MetricSummary] = Field(default_factory=list)
    missing_metrics: List[str] = Field(default_factory=list)
    completeness_score: float = Field(..., ge=0.0, le=1.0)


class ActivePathwayResponse(BaseModel):
    pathway_id: str
    summary: str
    nodes: List[str]
    chain_length: int
    confidence: str


class OverallConfidence(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    level: str = Field(..., description="'High' | 'Moderate' | 'Preliminary'")
    explanation: str


class StructuredReportResponse(BaseModel):
    """
    Comprehensive, scientifically grounded ecological report.
    Usable both as the structured payload of a chat response and as a standalone export.
    """
    conversation_id: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    profile_summary: ProfileSummaryResponse
    active_pathways: List[ActivePathwayResponse]
    recommendations: List[Recommendation]
    overall_confidence: OverallConfidence
    narrative_summary: str = Field(
        ...,
        description="2–4 sentences synthesizing the entire intervention suite into a cohesive strategy."
    )
    formatted_text: str = Field(
        ...,
        description="Clean, publication-ready Markdown rendering for land managers and UI display."
    )


class MissingInfoItem(BaseModel):
    field: str = Field(..., description="Target profile path, e.g., 'soil.organic_carbon_percent'")
    category: str = Field(..., description="High-level category: 'soil', 'climate', 'land', 'biodiversity'")
    question: str = Field(..., description="Polite, targeted follow-up question.")
    priority: int = Field(default=1, description="1 is highest priority")
    reason: str = Field(..., description="Ecological rationale for why this variable is needed")


class ChatResponse(BaseModel):
    """
    API Response model for POST /api/v1/chat.
    Maintains complete backwards compatibility for conversational chat client
    while providing the full typed report, narrative summary, and markdown view.
    """
    conversation_id: str
    turn_index: int = 1
    message: str
    needs_clarification: bool = False
    missing_information: List[MissingInfoItem] = Field(default_factory=list)
    profile_summary: Dict[str, Any] = Field(default_factory=dict)
    extracted_variables: Dict[str, Any] = Field(default_factory=dict)
    active_stress_pathways: List[Any] = Field(default_factory=list)
    retrieved_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
    report: Optional[StructuredReportResponse] = None
    formatted_text: Optional[str] = None
    narrative_summary: Optional[str] = None
    overall_confidence: Optional[OverallConfidence] = None
