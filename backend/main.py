"""
FastAPI Backend for Beacon Prototype

Tenet #3: Explicit Over Clever - Simple, traceable API
Tenet #10: Observable Systems - All endpoints instrumented
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog
import hashlib
import sys
import os
import json
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import (
    get_db, init_db, Conversation, CrisisEvent, 
    Student, ConversationTheme, ConversationSummary
)
from src.orchestrator import ConsensusOrchestrator, ConsensusConfig
from src.safety.safety_analyzer import SafetyService
from src.reasoning.mistral_reasoner import MistralReasoner
from src.reasoning.strategies import ExpertLLMStrategy
from src.conversation import ConversationAgent, ConversationContext
from src.orchestrator.agent_graph import CouncilGraph

# Initialize logging
logger = structlog.get_logger()

# ... (FastAPI setup) ...

# Initialize FastAPI app
app = FastAPI(
    title="Beacon API",
    description="Mental health AI triage system",
    version="0.1.0"
)

# CORS middleware (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:3002"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (singleton pattern)
safety_analyzer = None
mistral_reasoner = None
orchestrator = None
conversation_agent = None
council_graph = None  # New Council Graph
rag_service = None  # RAG service for indexing


def hash_pii(pii: str) -> str:
    """Hash PII for logging (Tenet #2)."""
    return hashlib.sha256(pii.encode()).hexdigest()[:16]


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global safety_analyzer, mistral_reasoner, orchestrator, conversation_agent, council_graph, rag_service
    
    logger.info("initializing_services")
    
    # Initialize database
    init_db()
    logger.info("database_initialized")
    
    # Initialize services
    try:
        # Path to config from backend directory
        config_path = Path(__file__).parent.parent / "config" / "crisis_patterns.yaml"
        safety_analyzer = SafetyService(patterns_path=str(config_path))
        logger.info("safety_service_initialized")
        
        # Use Expert Strategy (Mistral 7B) for the Clinical Reasoner
        mistral_reasoner = MistralReasoner(strategy=ExpertLLMStrategy())
        logger.info("mistral_reasoner_initialized", strategy="ExpertLLMStrategy")
        
        orchestrator = ConsensusOrchestrator(
            safety_service=safety_analyzer,
            mistral_reasoner=mistral_reasoner,
            config=ConsensusConfig()
        )
        logger.info("orchestrator_initialized")
        
        # Initialize conversation agent with RAG
        try:
            conversation_agent = ConversationAgent(use_rag=True)
            logger.info("conversation_agent_initialized", rag_enabled=True)
        except RuntimeError as e:
            logger.error("conversation_agent_initialization_failed", error=str(e))
            raise
            
        # Initialize Council Graph (The new Agentic Workflow)
        council_graph = CouncilGraph(
            safety_service=safety_analyzer,
            mistral_reasoner=mistral_reasoner,
            conversation_agent=conversation_agent
        )
        logger.info("council_graph_initialized")
        
        # Initialize RAG service for indexing
        try:
            from src.rag.rag_service import RAGService
            rag_service = RAGService()
            logger.info("rag_service_initialized")
        except Exception as e:
            logger.warning("rag_service_initialization_failed", error=str(e))
            rag_service = None
        
    except Exception as e:
        logger.error("service_initialization_failed", error=str(e), exc_info=True)
        raise


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request from student."""
    session_id: str
    message: str
    student_id: Optional[str] = None  # Optional student identifier


class StudentCreate(BaseModel):
    """Create student profile."""
    student_id: str  # Unhashed ID (will be hashed server-side)
    name: str
    grade: Optional[str] = None
    preferred_name: Optional[str] = None
    communication_style: Optional[str] = "casual"


class StudentProfile(BaseModel):
    """Student profile response."""
    id: int
    student_id_hash: str
    name: str
    grade: Optional[str]
    preferred_name: Optional[str]
    communication_style: Optional[str]
    created_at: str
    last_active: str
    total_conversations: int


class ThemeResponse(BaseModel):
    """Conversation theme response."""
    id: int
    theme: str
    description: Optional[str]
    first_mentioned: str
    last_mentioned: str
    mention_count: int
    is_active: bool
    resolved: bool


class ChatResponse(BaseModel):
    """Chat response to student."""
    response: str
    risk_level: str
    is_crisis: bool
    conversation_id: int


class ConversationDetail(BaseModel):
    """Detailed conversation for counselor view."""
    id: int
    session_id_hash: str
    message: str
    response: str
    risk_level: str
    risk_score: float
    regex_score: float
    semantic_score: float
    mistral_score: Optional[float]
    reasoning: str
    matched_patterns: List[str]
    latency_ms: int
    timeout_occurred: bool
    created_at: str


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Beacon API",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "safety_analyzer": safety_analyzer is not None,
            "mistral_reasoner": mistral_reasoner is not None,
            "orchestrator": orchestrator is not None
        }
    }


# ============================================================================
# STUDENT PROFILE ENDPOINTS
# ============================================================================

@app.post("/students", response_model=StudentProfile)
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    """
    Create or update student profile.
    
    Tenet #8: Engagement - Build student profiles for personalized interaction
    """
    student_id_hash = hash_pii(student.student_id)
    
    # Check if student exists
    existing = db.query(Student).filter(
        Student.student_id_hash == student_id_hash
    ).first()
    
    if existing:
        # Update existing profile
        existing.name = student.name
        existing.grade = student.grade
        existing.preferred_name = student.preferred_name
        existing.communication_style = student.communication_style
        existing.last_active = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        
        logger.info(
            "student_profile_updated",
            student_id=student_id_hash
        )
        
        return StudentProfile(**existing.to_dict())
    
    # Create new student
    new_student = Student(
        student_id_hash=student_id_hash,
        name=student.name,
        grade=student.grade,
        preferred_name=student.preferred_name,
        communication_style=student.communication_style
    )
    
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    
    logger.info(
        "student_profile_created",
        student_id=student_id_hash
    )
    
    return StudentProfile(**new_student.to_dict())


@app.get("/students", response_model=List[StudentProfile])
async def list_students(
    db: Session = Depends(get_db)
):
    """
    List all students (counselor dashboard).
    
    Tenet #9: Visibility - Counselors can see all their students
    """
    students = db.query(Student).order_by(
        Student.last_active.desc()
    ).all()
    
    return [StudentProfile(**s.to_dict()) for s in students]


@app.get("/students/{student_id}", response_model=StudentProfile)
async def get_student(
    student_id: str,
    db: Session = Depends(get_db)
):
    """Get student profile by ID."""
    student_id_hash = hash_pii(student_id)
    
    student = db.query(Student).filter(
        Student.student_id_hash == student_id_hash
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return StudentProfile(**student.to_dict())


@app.get("/students/hash/{student_id_hash}", response_model=StudentProfile)
async def get_student_by_hash(
    student_id_hash: str,
    db: Session = Depends(get_db)
):
    """Get student profile by hash (internal use)."""
    student = db.query(Student).filter(
        Student.student_id_hash == student_id_hash
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return StudentProfile(**student.to_dict())


@app.get("/students/hash/{student_id_hash}/themes", response_model=List[ThemeResponse])
async def get_student_themes(
    student_id_hash: str,
    db: Session = Depends(get_db)
):
    """
    Get ongoing conversation themes for a student.
    
    Tenet #8: Engagement - Track what matters to the student
    """
    themes = db.query(ConversationTheme).filter(
        ConversationTheme.student_id_hash == student_id_hash,
        ConversationTheme.is_active == 1
    ).order_by(ConversationTheme.last_mentioned.desc()).all()
    
    return [ThemeResponse(**t.to_dict()) for t in themes]


@app.get("/students/hash/{student_id_hash}/conversations", response_model=List[ConversationDetail])
async def get_student_conversations(
    student_id_hash: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get all conversations for a student.
    
    Combines all sessions for this student.
    """
    # For now, we'll need to track student_id_hash in conversations
    # This will be updated when we link sessions to students
    conversations = db.query(Conversation).filter(
        Conversation.session_id_hash == student_id_hash
    ).order_by(Conversation.created_at.desc()).limit(limit).all()
    
    return [
        ConversationDetail(
            id=conv.id,
            session_id_hash=conv.session_id_hash,
            message=conv.message,
            response=conv.response,
            risk_level=conv.risk_level,
            risk_score=conv.risk_score,
            regex_score=conv.regex_score,
            semantic_score=conv.semantic_score,
            mistral_score=conv.mistral_score,
            reasoning=conv.reasoning,
            matched_patterns=json.loads(conv.matched_patterns) if isinstance(conv.matched_patterns, str) else conv.matched_patterns,
            latency_ms=conv.latency_ms,
            timeout_occurred=bool(conv.timeout_occurred),
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Process student message and return response.
    
    Tenet #1: Safety First - Crisis detection runs in parallel
    Tenet #9: Visibility - All decisions logged
    """
    session_id_hash = hash_pii(request.session_id)
    
    logger.info(
        "chat_request_received",
        session_id=session_id_hash,
        message_length=len(request.message)
    )
    
    try:
        # Get or create student profile if student_id provided
        student_id_hash = None
        student_profile = None
        
        if request.student_id:
            student_id_hash = hash_pii(request.student_id)
            student_profile = db.query(Student).filter(
                Student.student_id_hash == student_id_hash
            ).first()
            
            if student_profile:
                # Update last active
                student_profile.last_active = datetime.utcnow()
                student_profile.total_conversations += 1
                db.commit()
        
        # Get history (use student_id_hash if available, otherwise session_id_hash)
        lookup_hash = student_id_hash if student_id_hash else session_id_hash
        conversation_history = _get_conversation_history(db, lookup_hash, limit=10)
        
        # Get active themes for context
        active_themes = []
        if student_id_hash:
            themes = db.query(ConversationTheme).filter(
                ConversationTheme.student_id_hash == student_id_hash,
                ConversationTheme.is_active == 1
            ).order_by(ConversationTheme.last_mentioned.desc()).limit(3).all()
            active_themes = [t.theme for t in themes]
        
        # Build enhanced context for LLM
        context_info = {
            "student_name": student_profile.preferred_name or student_profile.name if student_profile else None,
            "active_themes": active_themes,
            "conversation_count": len(conversation_history) // 2
        }
        
        # Execute Council Graph
        graph_result = await council_graph.run(
            message=request.message,
            session_id=request.session_id,
            history=conversation_history
        )
        
        # Extract results
        response_text = graph_result["final_response"]
        risk_level = graph_result["risk_level"]
        is_crisis = graph_result["is_crisis"]
        matched_patterns = graph_result.get("matched_patterns", [])
        
        # Save to database
        conversation = Conversation(
            session_id_hash=session_id_hash,
            message=request.message,
            response=response_text,
            risk_level=risk_level,
            risk_score=graph_result["safety_result"].p_regex if graph_result["safety_result"] else 0.0,
            regex_score=graph_result["safety_result"].p_regex if graph_result["safety_result"] else 0.0,
            semantic_score=graph_result["safety_result"].p_semantic if graph_result["safety_result"] else 0.0,
            mistral_score=graph_result["mistral_result"].p_mistral if graph_result["mistral_result"] else None,
            reasoning=f"Trace: {graph_result['trace_steps']}",
            matched_patterns=matched_patterns,
            latency_ms=1000,
            timeout_occurred=0
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # Log crisis event if needed
        if is_crisis:
            crisis_event = CrisisEvent(
                session_id_hash=session_id_hash,
                conversation_id=conversation.id,
                risk_score=0.99,
                matched_patterns=matched_patterns,
                reasoning=str(graph_result["trace_steps"])
            )
            db.add(crisis_event)
            db.commit()
            
            logger.warning(
                "crisis_event_logged",
                session_id=session_id_hash,
                conversation_id=conversation.id,
                risk_score=0.99
            )
        
        logger.info(
            "chat_response_sent",
            session_id=session_id_hash,
            conversation_id=conversation.id,
            risk_level=risk_level,
            latency_ms=0
        )
        
        return ChatResponse(
            response=response_text,
            risk_level=risk_level,
            is_crisis=is_crisis,
            conversation_id=conversation.id
        )
        
    except Exception as e:
        logger.error(
            "chat_request_failed",
            session_id=session_id_hash,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{session_id}", response_model=List[ConversationDetail])
async def get_conversations(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get conversation history for a session (counselor view).
    
    Tenet #9: Visibility - Counselors can see reasoning traces
    """
    session_id_hash = hash_pii(session_id)
    
    conversations = db.query(Conversation).filter(
        Conversation.session_id_hash == session_id_hash
    ).order_by(Conversation.created_at.desc()).limit(50).all()
    
    return [
        ConversationDetail(
            id=conv.id,
            session_id_hash=conv.session_id_hash,
            message=conv.message,
            response=conv.response,
            risk_level=conv.risk_level,
            risk_score=conv.risk_score,
            regex_score=conv.regex_score,
            semantic_score=conv.semantic_score,
            mistral_score=conv.mistral_score,
            reasoning=conv.reasoning,
            matched_patterns=conv.matched_patterns,
            latency_ms=conv.latency_ms,
            timeout_occurred=bool(conv.timeout_occurred),
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]


@app.get("/conversations/lookup/{session_id_hash}", response_model=List[ConversationDetail])
async def get_conversations_by_hash(
    session_id_hash: str,
    db: Session = Depends(get_db)
):
    """
    Get conversation history by direct hash lookup (for internal/dashboard use).
    """
    conversations = db.query(Conversation).filter(
        Conversation.session_id_hash == session_id_hash
    ).order_by(Conversation.created_at.desc()).limit(50).all()
    
    return [
        ConversationDetail(
            id=conv.id,
            session_id_hash=conv.session_id_hash,
            message=conv.message,
            response=conv.response,
            risk_level=conv.risk_level,
            risk_score=conv.risk_score,
            regex_score=conv.regex_score,
            semantic_score=conv.semantic_score,
            mistral_score=conv.mistral_score,
            reasoning=conv.reasoning,
            matched_patterns=conv.matched_patterns,
            latency_ms=conv.latency_ms,
            timeout_occurred=bool(conv.timeout_occurred),
            created_at=conv.created_at.isoformat()
        )
        for conv in conversations
    ]


@app.get("/crisis-events", response_model=List[dict])
async def get_crisis_events(
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get recent crisis events (counselor dashboard).
    
    Tenet #2: Immutable audit trail
    """
    events = db.query(CrisisEvent).order_by(
        CrisisEvent.detected_at.desc()
    ).limit(limit).all()
    
    # Parse matched_patterns from JSON string to list
    result = []
    for event in events:
        event_dict = event.to_dict()
        if isinstance(event_dict['matched_patterns'], str):
            event_dict['matched_patterns'] = json.loads(event_dict['matched_patterns'])
        result.append(event_dict)
    
    return result


@app.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation_by_id(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single conversation by ID (for crisis event details).
    
    Tenet #9: Visibility and Explainability
    """
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "id": conversation.id,
        "session_id_hash": conversation.session_id_hash,
        "message": conversation.message,
        "response": conversation.response,
        "risk_level": conversation.risk_level,
        "risk_score": conversation.risk_score,
        "regex_score": conversation.regex_score,
        "semantic_score": conversation.semantic_score,
        "mistral_score": conversation.mistral_score,
        "reasoning": conversation.reasoning,
        "matched_patterns": json.loads(conversation.matched_patterns) if isinstance(conversation.matched_patterns, str) else conversation.matched_patterns,
        "latency_ms": conversation.latency_ms,
        "timeout_occurred": bool(conversation.timeout_occurred),
        "created_at": conversation.created_at.isoformat()
    }


@app.get("/test-stream")
async def test_stream():
    """Test streaming to verify it works."""
    async def generate():
        for i in range(5):
            yield f"data: {json.dumps({'count': i, 'message': f'Test {i}'})}\n\n"
            await asyncio.sleep(0.5)
        yield f"data: {json.dumps({'done': True})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


class ChatStreamRequest(BaseModel):
    """Chat stream request with optional flags."""
    session_id: str
    message: str
    student_id: Optional[str] = None
    skip_response: Optional[bool] = False  # For Consensus Demo


@app.post("/chat/stream")
async def chat_stream(
    request: ChatStreamRequest,
    db: Session = Depends(get_db)
):
    """
    Stream chat response with REAL-TIME risk assessment.
    
    Tenet #1: Safety First - Detect crisis DURING generation, not after
    Tenet #8: Engagement - "Thinking" animation builds trust during processing
    Tenet #9: Visibility - Show risk scores updating in real-time
    Tenet #15: Performance - Consensus scoring <50ms, response can take longer
    """
    session_id_hash = hash_pii(request.session_id)
    
    async def generate_stream():
        try:
            # Get conversation history
            student_id_hash = None
            if request.student_id:
                student_id_hash = hash_pii(request.student_id)
            
            lookup_hash = student_id_hash if student_id_hash else session_id_hash
            conversation_history = _get_conversation_history(db, lookup_hash, limit=10)
            
            # STEP 1: Start analysis
            yield f"data: {json.dumps({'type': 'thinking', 'message': 'Analyzing message...'})}\n\n"
            
            # STEP 2: FAST Consensus Analysis (regex + semantic + mistral scoring)
            # This should complete in <50ms for regex+semantic, <15s with mistral
            analysis_result = await council_graph.analyze_fast(
                message=request.message,
                session_id=request.session_id,
                history=conversation_history
            )
            
            # STEP 3: Send risk scores as they're available
            safety_result = analysis_result["safety_result"]
            if safety_result:
                yield f"data: {json.dumps({
                    'type': 'risk_score',
                    'layer': 'regex',
                    'score': float(safety_result.p_regex),
                    'patterns': safety_result.matched_patterns,
                    'latency_ms': 0
                })}\n\n"
                
                yield f"data: {json.dumps({
                    'type': 'risk_score',
                    'layer': 'semantic',
                    'score': float(safety_result.p_semantic),
                    'patterns': [],
                    'latency_ms': 0
                })}\n\n"
            
            mistral_result = analysis_result.get("mistral_result")
            if mistral_result:
                yield f"data: {json.dumps({
                    'type': 'risk_score',
                    'layer': 'mistral',
                    'score': float(mistral_result.p_mistral),
                    'patterns': [m.category for m in mistral_result.clinical_markers],
                    'latency_ms': 0,
                    'timeout': False
                })}\n\n"
            else:
                yield f"data: {json.dumps({
                    'type': 'risk_score',
                    'layer': 'mistral',
                    'score': 0.0,
                    'patterns': [],
                    'latency_ms': 0,
                    'timeout': True
                })}\n\n"
            
            # STEP 4: Send consensus verdict IMMEDIATELY
            final_score = analysis_result["final_score"]
            risk_level = analysis_result["risk_level"]
            is_crisis = analysis_result["is_crisis"]
            
            logger.info(
                "sending_consensus_verdict",
                final_score=float(final_score),
                risk_level=risk_level,
                is_crisis=is_crisis,
                regex_score=float(safety_result.p_regex) if safety_result else 0.0,
                semantic_score=float(safety_result.p_semantic) if safety_result else 0.0,
                mistral_score=float(mistral_result.p_mistral) if mistral_result else 0.0,
                mistral_timeout=mistral_result is None
            )
            
            yield f"data: {json.dumps({
                'type': 'consensus_verdict',
                'risk_level': risk_level,
                'final_score': float(final_score),
                'is_crisis': is_crisis,
                'total_latency_ms': analysis_result["latency_ms"]
            })}\n\n"
            
            # STEP 5: If crisis, send alert IMMEDIATELY
            if is_crisis:
                yield f"data: {json.dumps({'type': 'crisis_alert', 'message': 'CRISIS DETECTED - Counselor notified'})}\n\n"
                logger.warning(
                    "crisis_alert_sent",
                    session_id=session_id_hash,
                    risk_score=float(final_score)
                )
            
            # STEP 6: Generate response (or skip for demo)
            if request.skip_response:
                # For Consensus Demo - skip response generation
                response_text = "[Response generation skipped for demo - scoring only]"
                logger.info("response_generation_skipped", reason="demo_mode")
            else:
                # STEP 6: NOW generate response (this can take 120s)
                yield f"data: {json.dumps({'type': 'thinking', 'message': 'Connor is thinking...'})}\n\n"
                
                response_text = await council_graph.generate_response(
                    message=request.message,
                    session_id=request.session_id,
                    history=conversation_history,
                    analysis_result=analysis_result,
                    student_id_hash=student_id_hash  # Pass for RAG retrieval
                )
                
                # STEP 7: Stream response word by word (typing effect)
                words = response_text.split()
                for i, word in enumerate(words):
                    yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
                    await asyncio.sleep(0.04 if len(word) < 5 else 0.06)
            
            # STEP 8: Save to database
            conversation = Conversation(
                session_id_hash=session_id_hash,
                message=request.message,
                response=response_text,
                risk_level=risk_level,
                risk_score=float(final_score),
                regex_score=float(safety_result.p_regex) if safety_result else 0.0,
                semantic_score=float(safety_result.p_semantic) if safety_result else 0.0,
                mistral_score=float(mistral_result.p_mistral) if mistral_result else None,
                reasoning=f"Final Score: {final_score:.4f}, Risk: {risk_level}",
                matched_patterns=analysis_result["matched_patterns"],
                latency_ms=analysis_result["latency_ms"],
                timeout_occurred=mistral_result is None
            )
            
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            
            # Index conversation in RAG for future retrieval
            if rag_service and student_id_hash:
                try:
                    rag_service.index_conversation(
                        conversation_id=str(conversation.id),
                        student_id_hash=student_id_hash,
                        message=request.message,
                        response=response_text,
                        risk_level=risk_level,
                        timestamp=conversation.created_at
                    )
                    logger.info(
                        "conversation_indexed_in_rag",
                        conversation_id=conversation.id,
                        student_id=student_id_hash
                    )
                except Exception as e:
                    logger.warning("rag_indexing_failed", error=str(e))
            
            # Update student profile if available
            if student_id_hash:
                student_profile = db.query(Student).filter(
                    Student.student_id_hash == student_id_hash
                ).first()
                
                if student_profile:
                    student_profile.last_active = datetime.utcnow()
                    student_profile.total_conversations += 1
                    db.commit()
            
            if is_crisis:
                crisis_event = CrisisEvent(
                    session_id_hash=session_id_hash,
                    conversation_id=conversation.id,
                    risk_score=float(final_score),
                    matched_patterns=analysis_result["matched_patterns"],
                    reasoning=f"Consensus: {final_score:.4f}"
                )
                db.add(crisis_event)
                db.commit()
            
            # STEP 9: Send completion
            yield f"data: {json.dumps({
                'type': 'done',
                'conversation_id': conversation.id,
                'risk_level': risk_level,
                'is_crisis': is_crisis
            })}\n\n"
            
        except Exception as e:
            logger.error("stream_failed", error=str(e), exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


def _get_crisis_response() -> str:
    """
    Get deterministic crisis response.
    
    Tenet #1: Hard-coded crisis protocols that can't be overridden
    """
    return (
        "I'm really concerned about what you've shared. "
        "Your safety is the most important thing right now. "
        "I've notified your school counselor, and they'll reach out soon.\n\n"
        "In the meantime, here are some resources:\n\n"
        "🆘 National Suicide Prevention Lifeline: 988\n"
        "💬 Crisis Text Line: Text HOME to 741741\n"
        "🌐 Online Chat: https://suicidepreventionlifeline.org/chat/\n\n"
        "You're not alone in this. Help is available 24/7."
    )


def _get_service_unavailable_response() -> str:
    """
    Response when conversation service is temporarily unavailable.
    
    Tenet #11: Graceful degradation - show crisis resources
    """
    return (
        "I'm having trouble connecting right now, but I want to make sure you have support.\n\n"
        "If you need to talk to someone immediately:\n\n"
        "🆘 National Suicide Prevention Lifeline: 988\n"
        "💬 Crisis Text Line: Text HOME to 741741\n"
        "🌐 Online Chat: https://suicidepreventionlifeline.org/chat/\n\n"
        "Your school counselor is also available. Please reach out - you're not alone."
    )


def _get_conversation_history(
    db: Session,
    session_id_hash: str,
    limit: int = 5
) -> list[dict]:
    """
    Get recent conversation history for context.
    
    Args:
        db: Database session
        session_id_hash: Hashed session ID
        limit: Number of recent messages to retrieve
        
    Returns:
        List of conversation messages with role and content
    """
    conversations = db.query(Conversation).filter(
        Conversation.session_id_hash == session_id_hash
    ).order_by(Conversation.created_at.desc()).limit(limit).all()
    
    # Reverse to get chronological order
    conversations = list(reversed(conversations))
    
    history = []
    for conv in conversations:
        history.append({"role": "student", "content": conv.message})
        history.append({"role": "assistant", "content": conv.response})
    
    return history


def _determine_response_length(
    message: str,
    risk_score: float,
    conversation_history: list[dict]
) -> int:
    """
    Determine appropriate response length based on context.
    
    Tenet #8: Engagement Before Intervention - Match conversation style
    
    Args:
        message: Student's message
        risk_score: Risk assessment score
        conversation_history: Recent conversation history
        
    Returns:
        Max tokens for response generation
    """
    message_length = len(message.split())
    conversation_depth = len(conversation_history) // 2  # Divide by 2 (student + assistant pairs)
    
    # Short greeting or simple message -> short response
    # Expanded list of short inputs
    short_inputs = ['hi', 'hello', 'hey', 'sup', 'yo', 'ok', 'okay', 'thanks', 'cool']
    if message_length <= 3 or message.lower().strip() in short_inputs:
        return 60  # ~40 words - Keep it punchy
    
    # Early conversation (first 2 exchanges) -> brief, welcoming
    if conversation_depth < 1: # Only the very first exchange needs to be super short if input is longer
        return 90
    
    # High risk -> more detailed, supportive response
    if risk_score > 0.6:
        return 200  # Allow more space for comfort
    
    # Medium message -> medium response
    if message_length <= 20:
        return 100  # ~70-80 words
    
    # Long, detailed message -> comprehensive response
    return 180  # ~120-150 words


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
