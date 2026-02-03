"""
Retrieval Components for RAG

Tenet #8: Engagement Before Intervention - Provide relevant context
Tenet #9: Visibility - All retrievals logged
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
import structlog
from datetime import datetime, timedelta

from src.rag.vector_store import VectorStore, Document
from src.rag.embeddings import EmbeddingService

logger = structlog.get_logger()


@dataclass
class RetrievalResult:
    """Result from retrieval operation."""
    documents: List[Document]
    scores: List[float]
    query: str
    retrieval_time_ms: float
    
    def to_context(self, max_length: int = 2000) -> str:
        """
        Convert retrieved documents to context string.
        
        Args:
            max_length: Maximum context length
            
        Returns:
            Formatted context string
        """
        if not self.documents:
            return ""
        
        context_parts = []
        current_length = 0
        
        for doc, score in zip(self.documents, self.scores):
            # Format: [Score: 0.95] Content here...
            doc_text = f"[Relevance: {score:.2f}] {doc.content}"
            
            if current_length + len(doc_text) > max_length:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "\n\n".join(context_parts)


class ConversationRetriever:
    """
    Retrieve relevant past conversations for context.
    
    Tenet #8: Make Connor feel like a friend who remembers
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService
    ):
        """
        Initialize conversation retriever.
        
        Args:
            vector_store: Vector store for conversations
            embedding_service: Embedding service
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        
        logger.info("conversation_retriever_initialized")
    
    def index_conversation(
        self,
        conversation_id: str,
        student_id_hash: str,
        message: str,
        response: str,
        risk_level: str,
        timestamp: datetime
    ):
        """
        Index a conversation for retrieval.
        
        Args:
            conversation_id: Unique conversation ID
            student_id_hash: Hashed student ID
            message: Student's message
            response: Connor's response
            risk_level: Risk assessment
            timestamp: Conversation timestamp
        """
        # Combine message and response for context
        content = f"Student: {message}\nConnor: {response}"
        
        # Generate embedding
        embedding = self.embedding_service.embed(content)
        
        # Add to vector store
        self.vector_store.add_document(
            doc_id=conversation_id,
            content=content,
            embedding=embedding,
            metadata={
                "student_id_hash": student_id_hash,
                "risk_level": risk_level,
                "timestamp": timestamp.isoformat(),
                "type": "conversation"
            }
        )
        
        logger.debug(
            "conversation_indexed",
            conversation_id=conversation_id,
            student_id=student_id_hash,
            risk_level=risk_level
        )
    
    def retrieve_relevant_conversations(
        self,
        query: str,
        student_id_hash: str,
        top_k: int = 3,
        days_back: int = 30
    ) -> RetrievalResult:
        """
        Retrieve relevant past conversations.
        
        Args:
            query: Current message to find relevant context for
            student_id_hash: Student's hashed ID
            top_k: Number of conversations to retrieve
            days_back: Only retrieve conversations from last N days
            
        Returns:
            Retrieval result with relevant conversations
        """
        start_time = datetime.utcnow()
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed(query)
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Search with student filter
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more, then filter by date
            filter_metadata={"student_id_hash": student_id_hash, "type": "conversation"}
        )
        
        # Filter by date
        filtered_results = [
            (doc, score) for doc, score in results
            if datetime.fromisoformat(doc.metadata["timestamp"]) >= cutoff_date
        ][:top_k]
        
        # Extract documents and scores
        documents = [doc for doc, _ in filtered_results]
        scores = [score for _, score in filtered_results]
        
        retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "conversations_retrieved",
            student_id=student_id_hash,
            query_length=len(query),
            results_count=len(documents),
            retrieval_time_ms=retrieval_time
        )
        
        return RetrievalResult(
            documents=documents,
            scores=scores,
            query=query,
            retrieval_time_ms=retrieval_time
        )


class ResourceRetriever:
    """
    Retrieve mental health resources and coping strategies.
    
    Tenet #8: Provide evidence-based support
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService
    ):
        """
        Initialize resource retriever.
        
        Args:
            vector_store: Vector store for resources
            embedding_service: Embedding service
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        
        logger.info("resource_retriever_initialized")
    
    def index_resource(
        self,
        resource_id: str,
        title: str,
        content: str,
        category: str,
        tags: List[str]
    ):
        """
        Index a mental health resource.
        
        Args:
            resource_id: Unique resource ID
            title: Resource title
            content: Resource content
            category: Category (coping_strategy, crisis_resource, etc.)
            tags: Tags for filtering
        """
        # Combine title and content
        full_content = f"{title}\n\n{content}"
        
        # Generate embedding
        embedding = self.embedding_service.embed(full_content)
        
        # Add to vector store
        self.vector_store.add_document(
            doc_id=resource_id,
            content=full_content,
            embedding=embedding,
            metadata={
                "title": title,
                "category": category,
                "tags": tags,
                "type": "resource"
            }
        )
        
        logger.debug(
            "resource_indexed",
            resource_id=resource_id,
            category=category,
            tags=tags
        )
    
    def retrieve_relevant_resources(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> RetrievalResult:
        """
        Retrieve relevant mental health resources.
        
        Args:
            query: Query to find relevant resources for
            category: Optional category filter
            top_k: Number of resources to retrieve
            
        Returns:
            Retrieval result with relevant resources
        """
        start_time = datetime.utcnow()
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed(query)
        
        # Build metadata filter
        filter_metadata = {"type": "resource"}
        if category:
            filter_metadata["category"] = category
        
        # Search
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Extract documents and scores
        documents = [doc for doc, _ in results]
        scores = [score for _, score in results]
        
        retrieval_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "resources_retrieved",
            query_length=len(query),
            category=category,
            results_count=len(documents),
            retrieval_time_ms=retrieval_time
        )
        
        return RetrievalResult(
            documents=documents,
            scores=scores,
            query=query,
            retrieval_time_ms=retrieval_time
        )
    
    def load_default_resources(self):
        """Load default mental health resources."""
        default_resources = [
            {
                "id": "coping_breathing",
                "title": "Deep Breathing Exercise",
                "content": (
                    "When feeling anxious or overwhelmed, try this:\n"
                    "1. Breathe in slowly through your nose for 4 counts\n"
                    "2. Hold for 4 counts\n"
                    "3. Breathe out slowly through your mouth for 4 counts\n"
                    "4. Repeat 3-5 times\n\n"
                    "This activates your parasympathetic nervous system and helps calm your body."
                ),
                "category": "coping_strategy",
                "tags": ["anxiety", "stress", "quick_relief"]
            },
            {
                "id": "coping_grounding",
                "title": "5-4-3-2-1 Grounding Technique",
                "content": (
                    "When feeling overwhelmed or dissociating:\n"
                    "Name 5 things you can see\n"
                    "Name 4 things you can touch\n"
                    "Name 3 things you can hear\n"
                    "Name 2 things you can smell\n"
                    "Name 1 thing you can taste\n\n"
                    "This brings you back to the present moment."
                ),
                "category": "coping_strategy",
                "tags": ["anxiety", "panic", "grounding"]
            },
            {
                "id": "coping_journaling",
                "title": "Thought Journaling",
                "content": (
                    "When negative thoughts feel overwhelming:\n"
                    "1. Write down the thought\n"
                    "2. Ask: Is this thought based on facts or feelings?\n"
                    "3. Ask: What evidence supports or contradicts this thought?\n"
                    "4. Reframe: What's a more balanced way to think about this?\n\n"
                    "This is a core CBT technique for managing anxiety and depression."
                ),
                "category": "coping_strategy",
                "tags": ["depression", "anxiety", "cognitive"]
            },
            {
                "id": "crisis_988",
                "title": "988 Suicide & Crisis Lifeline",
                "content": (
                    "If you're thinking about suicide or in crisis:\n"
                    "Call or text 988 (available 24/7)\n\n"
                    "Trained counselors provide free, confidential support.\n"
                    "You don't have to be suicidal to call - they help with any emotional distress."
                ),
                "category": "crisis_resource",
                "tags": ["crisis", "suicide", "immediate_help"]
            },
            {
                "id": "crisis_text_line",
                "title": "Crisis Text Line",
                "content": (
                    "If you prefer texting:\n"
                    "Text HOME to 741741 (available 24/7)\n\n"
                    "Connect with a trained crisis counselor via text.\n"
                    "All conversations are confidential."
                ),
                "category": "crisis_resource",
                "tags": ["crisis", "text", "immediate_help"]
            },
            {
                "id": "sleep_hygiene",
                "title": "Sleep Hygiene Tips",
                "content": (
                    "Better sleep improves mood and reduces anxiety:\n"
                    "- Keep a consistent sleep schedule\n"
                    "- Avoid screens 1 hour before bed\n"
                    "- Keep bedroom cool and dark\n"
                    "- Avoid caffeine after 2pm\n"
                    "- Try relaxation exercises before bed\n\n"
                    "Sleep problems often worsen mental health symptoms."
                ),
                "category": "wellness_tip",
                "tags": ["sleep", "anxiety", "depression", "wellness"]
            },
            {
                "id": "social_connection",
                "title": "Building Social Connections",
                "content": (
                    "Social connection is protective for mental health:\n"
                    "- Reach out to one person today (text, call, or in-person)\n"
                    "- Join a club or activity you're interested in\n"
                    "- Volunteer for a cause you care about\n"
                    "- Practice active listening when others share\n\n"
                    "Even small interactions can reduce feelings of loneliness."
                ),
                "category": "wellness_tip",
                "tags": ["loneliness", "depression", "social"]
            },
            {
                "id": "academic_stress",
                "title": "Managing Academic Stress",
                "content": (
                    "When schoolwork feels overwhelming:\n"
                    "- Break large tasks into smaller steps\n"
                    "- Use a planner to track deadlines\n"
                    "- Take 5-minute breaks every 25 minutes (Pomodoro)\n"
                    "- Ask for help from teachers or tutors\n"
                    "- Remember: Grades don't define your worth\n\n"
                    "Perfectionism often makes stress worse."
                ),
                "category": "coping_strategy",
                "tags": ["academic_stress", "anxiety", "school"]
            }
        ]
        
        for resource in default_resources:
            self.index_resource(
                resource_id=resource["id"],
                title=resource["title"],
                content=resource["content"],
                category=resource["category"],
                tags=resource["tags"]
            )
        
        logger.info(
            "default_resources_loaded",
            count=len(default_resources)
        )
