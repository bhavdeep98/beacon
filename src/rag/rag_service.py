"""
RAG Service - Main interface for retrieval-augmented generation

Tenet #8: Engagement Before Intervention - Contextual, informed responses
Tenet #9: Visibility - All retrievals logged and traceable
"""

from typing import Dict, List, Optional
import structlog
from datetime import datetime

from src.rag.vector_store import VectorStore
from src.rag.embeddings import EmbeddingService
from src.rag.retriever import ConversationRetriever, ResourceRetriever, RetrievalResult

logger = structlog.get_logger()


class RAGService:
    """
    Main RAG service coordinating retrieval and context building.
    
    Provides Connor with:
    - Relevant past conversations
    - Mental health resources
    - Coping strategies
    - Crisis protocols
    """
    
    def __init__(self):
        """Initialize RAG service with all components."""
        # Initialize embedding service
        self.embedding_service = EmbeddingService()
        
        # Create separate vector stores for different content types
        self.conversation_store = VectorStore()
        self.resource_store = VectorStore()
        
        # Initialize retrievers
        self.conversation_retriever = ConversationRetriever(
            vector_store=self.conversation_store,
            embedding_service=self.embedding_service
        )
        
        self.resource_retriever = ResourceRetriever(
            vector_store=self.resource_store,
            embedding_service=self.embedding_service
        )
        
        # Load default resources
        self.resource_retriever.load_default_resources()
        
        logger.info(
            "rag_service_initialized",
            conversation_docs=self.conversation_store.get_stats()["total_documents"],
            resource_docs=self.resource_store.get_stats()["total_documents"]
        )
    
    def index_conversation(
        self,
        conversation_id: str,
        student_id_hash: str,
        message: str,
        response: str,
        risk_level: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Index a conversation for future retrieval.
        
        Args:
            conversation_id: Unique conversation ID
            student_id_hash: Hashed student ID
            message: Student's message
            response: Connor's response
            risk_level: Risk assessment
            timestamp: Conversation timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        self.conversation_retriever.index_conversation(
            conversation_id=conversation_id,
            student_id_hash=student_id_hash,
            message=message,
            response=response,
            risk_level=risk_level,
            timestamp=timestamp
        )
    
    def build_context(
        self,
        current_message: str,
        student_id_hash: str,
        include_conversations: bool = True,
        include_resources: bool = True,
        max_context_length: int = 2000
    ) -> Dict:
        """
        Build comprehensive context for LLM.
        
        Args:
            current_message: Current student message
            student_id_hash: Student's hashed ID
            include_conversations: Include past conversations
            include_resources: Include relevant resources
            max_context_length: Maximum context length
            
        Returns:
            Dictionary with context components
        """
        context = {
            "current_message": current_message,
            "past_conversations": "",
            "relevant_resources": "",
            "retrieval_stats": {}
        }
        
        # Retrieve past conversations
        if include_conversations:
            conv_result = self.conversation_retriever.retrieve_relevant_conversations(
                query=current_message,
                student_id_hash=student_id_hash,
                top_k=3,
                days_back=30
            )
            
            context["past_conversations"] = conv_result.to_context(
                max_length=max_context_length // 2
            )
            context["retrieval_stats"]["conversations"] = {
                "count": len(conv_result.documents),
                "retrieval_time_ms": conv_result.retrieval_time_ms
            }
        
        # Retrieve relevant resources
        if include_resources:
            resource_result = self.resource_retriever.retrieve_relevant_resources(
                query=current_message,
                top_k=2
            )
            
            context["relevant_resources"] = resource_result.to_context(
                max_length=max_context_length // 2
            )
            context["retrieval_stats"]["resources"] = {
                "count": len(resource_result.documents),
                "retrieval_time_ms": resource_result.retrieval_time_ms
            }
        
        logger.info(
            "context_built",
            student_id=student_id_hash,
            message_length=len(current_message),
            past_conversations_count=context["retrieval_stats"].get("conversations", {}).get("count", 0),
            resources_count=context["retrieval_stats"].get("resources", {}).get("count", 0)
        )
        
        return context
    
    def format_context_for_llm(self, context: Dict) -> str:
        """
        Format context dictionary into prompt string for LLM.
        
        Args:
            context: Context dictionary from build_context()
            
        Returns:
            Formatted context string
        """
        parts = []
        
        # Add past conversations if available
        if context.get("past_conversations"):
            parts.append("## Relevant Past Conversations")
            parts.append(context["past_conversations"])
        
        # Add resources if available
        if context.get("relevant_resources"):
            parts.append("## Relevant Mental Health Resources")
            parts.append(context["relevant_resources"])
        
        if not parts:
            return ""
        
        return "\n\n".join(parts)
    
    def get_crisis_resources(self) -> str:
        """
        Get immediate crisis resources.
        
        Returns:
            Formatted crisis resources string
        """
        result = self.resource_retriever.retrieve_relevant_resources(
            query="suicide crisis immediate help",
            category="crisis_resource",
            top_k=3
        )
        
        return result.to_context(max_length=1000)
    
    def get_coping_strategies(self, query: str) -> str:
        """
        Get relevant coping strategies.
        
        Args:
            query: Query describing the issue
            
        Returns:
            Formatted coping strategies
        """
        result = self.resource_retriever.retrieve_relevant_resources(
            query=query,
            category="coping_strategy",
            top_k=2
        )
        
        return result.to_context(max_length=1000)
    
    def get_stats(self) -> Dict:
        """Get RAG service statistics."""
        return {
            "conversation_store": self.conversation_store.get_stats(),
            "resource_store": self.resource_store.get_stats(),
            "embedding_cache": self.embedding_service.get_cache_stats()
        }
