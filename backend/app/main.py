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
    6. Returns structured response with profile summary, active pathways, and scientific citations.
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

        summary_items = [f"• {k.replace('_', ' ').title()}: {v}" for k, v in session.profile.to_summary_dict().items()]
        summary_str = "\n".join(summary_items)

        pathway_lines = []
        for p in active_pathways:
            pathway_lines.append(f"• **{p.pathway_id.upper()}**: `{p.summary}` ({p.confidence.value} confidence)")
        pathways_str = "\n".join(pathway_lines) if pathway_lines else "None detected (ecosystem indicators within healthy thresholds)."

        evidence_lines = []
        for ev in retrieved_evidence[:3]:
            evidence_lines.append(f"• **{ev.get('id')}**: *{ev.get('topic')}* — {ev.get('source')} ([Source]({ev.get('url')}))")
        evidence_str = "\n".join(evidence_lines) if evidence_lines else "No specific evidence filtered."

        # Generate multi-metric recommendations (one per pathway)
        recommendations = recommendation_generator.generate(
            profile=session.profile,
            pathways=active_pathways,
        )

        rec_lines = []
        for rec in recommendations:
            horizon_tag = f"[{rec.time_horizon.upper()}]"
            conf_tag = f"conf={rec.confidence_score:.2f}"
            rec_lines.append(
                f"• {horizon_tag} **{rec.recommendation[:120]}{'...' if len(rec.recommendation) > 120 else ''}** "
                f"— affects: `{'`, `'.join(rec.affected_metrics[:3])}`  ({conf_tag})"
            )
        recs_str = "\n".join(rec_lines) if rec_lines else "No recommendations generated (insufficient evidence coverage)."

        response_text = (
            f"**Environmental Profile Established:**\n\n{summary_str}\n\n"
            f"**Active Ecological Stress Pathways ({len(active_pathways)} detected):**\n{pathways_str}\n\n"
            f"**Retrieved Scientific Grounding ({len(retrieved_evidence)} sources):**\n{evidence_str}\n\n"
            f"**Evidence-Backed Recommendations ({len(recommendations)} generated):**\n{recs_str}"
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
        active_stress_pathways=active_pathways,
        retrieved_evidence=retrieved_evidence,
        recommendations=recommendations,
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
