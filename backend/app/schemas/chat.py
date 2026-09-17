from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.profile import EnvironmentalProfile

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, description="Unique conversation session ID. If omitted, a new one is created.")
    message: str = Field(..., min_length=1, description="User input message describing their land, soil, climate, or biodiversity situation.")

class MissingInfoItem(BaseModel):
    field: str = Field(..., description="Target profile path, e.g., 'soil.organic_carbon_percent'")
    category: str = Field(..., description="High-level category: 'soil', 'climate', 'land', 'biodiversity'")
    question: str = Field(..., description="Polite, targeted follow-up question.")
    priority: int = Field(default=1, description="1 is highest priority")
    reason: str = Field(..., description="Ecological rationale for why this variable is needed")

class ChatResponse(BaseModel):
    conversation_id: str
    turn_index: int
    message: str
    needs_clarification: bool = False
    missing_information: List[MissingInfoItem] = Field(default_factory=list)
    profile_summary: Dict[str, Any] = Field(default_factory=dict)
    extracted_variables: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
