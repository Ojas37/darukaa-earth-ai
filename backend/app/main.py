import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.profile import EnvironmentalProfile
from app.services.extractor import EnvironmentalExtractor
from app.services.clarification import ClarificationEngine
from app.memory.session import session_manager

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("daruka.app")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Biodiversity Intelligence System — Grounded Environmental Reasoning & Evidence Retrieval"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

extractor = EnvironmentalExtractor()
clarification_engine = ClarificationEngine()

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment
    }

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Conversational AI"])
async def chat_turn(request: ChatRequest):
    """
    Main conversational endpoint:
    1. Retrieves/creates conversation session.
    2. Extracts structured environmental variables from natural language.
    3. Merges new variables into persistent EnvironmentalProfile.
    4. Evaluates if critical missing variables require clarification.
    5. Returns response with structured extraction and clarification prompt.
    """
    session = session_manager.get_or_create_session(request.conversation_id)
    session.add_message(role="user", content=request.message)

    # 1. Extract environmental variables and merge with session profile
    updated_profile = extractor.extract(text=request.message, existing_profile=session.profile)
    session.profile = updated_profile

    # 2. Evaluate missing critical variables
    needs_clarification, missing_items, clarification_prompt = clarification_engine.evaluate(session.profile)

    # 3. Construct response message
    if needs_clarification:
        response_text = clarification_prompt
    else:
        summary_items = [f"• {k.replace('_', ' ').title()}: {v}" for k, v in session.profile.to_summary_dict().items()]
        summary_str = "\n".join(summary_items)
        response_text = (
            f"**Environmental Profile Established:**\n\n{summary_str}\n\n"
            f"Sufficient environmental parameters are present to initiate multi-metric ecological reasoning and scientific evidence retrieval."
        )

    session.add_message(role="assistant", content=response_text)
    session_manager.save_session(session)

    return ChatResponse(
        conversation_id=session.conversation_id,
        turn_index=len(session.messages) // 2,
        message=response_text,
        needs_clarification=needs_clarification,
        missing_information=missing_items,
        profile_summary=session.profile.to_summary_dict(),
        extracted_variables=session.profile.model_dump(exclude_none=True),
        recommendations=[],
        clarification_prompt=clarification_prompt
    )

@app.get("/api/v1/environment/{conversation_id}", response_model=EnvironmentalProfile, tags=["Environmental Profile"])
async def get_environment_profile(conversation_id: str):
    """Retrieves the full structured environmental profile for a given conversation."""
    session = session_manager.get_or_create_session(conversation_id)
    return session.profile

@app.post("/api/v1/environment/extract", tags=["Environmental Profile"])
async def extract_variables_direct(payload: dict):
    """Utility endpoint to extract structured variables directly from raw text."""
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="Text field is required")
    profile = extractor.extract(text)
    return {
        "summary": profile.to_summary_dict(),
        "profile": profile.model_dump()
    }

@app.delete("/api/v1/conversations/{conversation_id}", tags=["Conversational AI"])
async def reset_conversation(conversation_id: str):
    """Resets or deletes a conversation session."""
    deleted = session_manager.delete_session(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation session not found")
    return {"status": "deleted", "conversation_id": conversation_id}
