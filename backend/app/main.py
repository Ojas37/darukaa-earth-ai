import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.profile import EnvironmentalProfile
from app.services.extractor import EnvironmentalExtractor
from app.services.clarification import ClarificationEngine
from app.reasoning.relationship_graph import relationship_graph, StressPathway
from app.rag.retrieval import evidence_retriever
from app.rag.validation import claim_validator
from app.memory.session import session_manager
from app.recommendations.generator import recommendation_generator, Recommendation

from app.schemas.response import StructuredReportResponse, ProfileSummaryResponse, OverallConfidence
from app.recommendations.formatter import build_structured_report

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
        "environment": settings.environment,
        "rag_collection_count": evidence_retriever.collection.count()
    }

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Conversational AI"])
async def chat_turn(request: ChatRequest):
    """
    Main conversational endpoint:
    1. Retrieves/creates conversation session.
    2. Extracts structured environmental variables from natural language.
    3. Merges new variables into persistent EnvironmentalProfile.
    4. Evaluates if critical missing variables require clarification.
    5. If sufficient info is present:
       a. Evaluates active causal stress pathways via Environmental Relationship Graph.
       b. Retrieves peer-reviewed scientific evidence filtered by biome, climate, and active edge IDs.
       c. Generates multi-metric, evidence-constrained recommendations.
       d. Compiles comprehensive StructuredReportResponse.
    6. Returns structured response with chat bubble text, structured report, and markdown view.
    """
    session = session_manager.get_or_create_session(request.conversation_id)
    session.add_message(role="user", content=request.message)

    # 1. Extract environmental variables and merge with session profile
    updated_profile = extractor.extract(text=request.message, existing_profile=session.profile)
    session.profile = updated_profile

    # 2. Evaluate missing critical variables
    needs_clarification, missing_items, clarification_prompt = clarification_engine.evaluate(session.profile)

    active_pathways: list[StressPathway] = []
    retrieved_evidence: list[dict] = []
    recommendations: list[Recommendation] = []
    report: Optional[StructuredReportResponse] = None

    # 3. Construct response message
    if needs_clarification:
        response_text = clarification_prompt
    else:
        # Discover active multi-edge stress pathways
        active_pathways = relationship_graph.find_stress_pathways(session.profile, min_length=2)
        
        # Collect active edge IDs across all discovered pathways
        active_edge_ids = list(set([edge.id for p in active_pathways for edge in p.edges]))

        # Retrieve relevant scientific evidence filtered by profile context & active edge IDs
        retrieved_evidence = evidence_retriever.retrieve(
            query=f"biodiversity restoration soil organic carbon management in {session.profile.location.biome or 'cropland'}",
            biome=session.profile.location.biome,
            climate_zone=str(session.profile.climate.rainfall_pattern.value) if session.profile.climate.rainfall_pattern.is_known else None,
            edge_ids=active_edge_ids if active_edge_ids else None,
            top_k=5
        )

        # Generate multi-metric recommendations (one per pathway)
        recommendations = recommendation_generator.generate(
            profile=session.profile,
            pathways=active_pathways,
        )

        # Build complete typed and formatted report
        report = build_structured_report(
            conversation_id=session.conversation_id,
            profile=session.profile,
            pathways=active_pathways,
            recommendations=recommendations,
        )
        session.latest_report_json = report.model_dump_json()
        response_text = report.formatted_text

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
        active_stress_pathways=active_pathways,
        retrieved_evidence=retrieved_evidence,
        recommendations=recommendations,
        clarification_prompt=clarification_prompt,
        report=report,
        formatted_text=report.formatted_text if report else None,
        narrative_summary=report.narrative_summary if report else None,
        overall_confidence=report.overall_confidence if report else None,
    )

@app.get("/api/v1/report/{conversation_id}", response_model=StructuredReportResponse, tags=["Reports"])
async def get_report(conversation_id: str):
    """
    Generates and returns the full standalone StructuredReportResponse for a conversation
    without requiring a chat turn. Returns cached report if already generated.
    """
    session = session_manager.get_or_create_session(conversation_id)
    if session.latest_report_json:
        return StructuredReportResponse.model_validate_json(session.latest_report_json)

    if not session.messages and not any(v.is_known for v in session.profile.soil.__dict__.values() if hasattr(v, "is_known")):
        raise HTTPException(status_code=404, detail=f"No active environmental profile found for session '{conversation_id}'")

    active_pathways = relationship_graph.find_stress_pathways(session.profile, min_length=2)
    recommendations = recommendation_generator.generate(
        profile=session.profile,
        pathways=active_pathways,
    )

    report = build_structured_report(
        conversation_id=session.conversation_id,
        profile=session.profile,
        pathways=active_pathways,
        recommendations=recommendations,
    )
    session.latest_report_json = report.model_dump_json()
    session_manager.save_session(session)
    return report

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
