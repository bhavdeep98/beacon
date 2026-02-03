"""
Conversational AI Agent for Mental Health Support

Tenet #1: Safety First - Crisis detection runs in parallel
Tenet #3: Explicit Over Clever - Clear, traceable conversation flow
Tenet #4: Fail Loud, Fail Early - No silent fallbacks
Tenet #8: Engagement Before Intervention - Build trust through empathy
Tenet #11: Graceful Degradation - Native Llama with automatic VRAM optimization
"""

from typing import TypedDict, Annotated, Sequence, Optional, Iterator
from dataclasses import dataclass
import structlog
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = structlog.get_logger()

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    logger.warning("llama_cpp_not_available", reason="llama-cpp-python not installed - using mock mode")
    LLAMA_CPP_AVAILABLE = False

# Import GPU utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.gpu_utils import calculate_optimal_layers, get_gpu_info


def sanitize_llm_output(text: str) -> str:
    """
    Removes non-printable ASCII characters and 'alphabet soup' 
    while preserving standard punctuation and spacing.
    """
    if not text:
        return ""

    # 1. Strip common LLM artifacts like <unk> or </s>
    artifacts = ["<unk>", "</s>", "<|endoftext|>", "[/INST]"]
    for artifact in artifacts:
        text = text.replace(artifact, "")

    # 2. Regex to keep only printable characters (ASCII 32-126) 
    # and common whitespace (newlines, tabs)
    # [^\x20-\x7E\t\n\r] matches anything NOT in the printable range
    clean_text = re.sub(r'[^\x20-\x7E\t\n\r]', '', text)

    return clean_text.strip()


@dataclass(frozen=True)
class ConversationContext:
    """Immutable conversation context."""
    session_id: str
    risk_level: str
    risk_score: float
    matched_patterns: list[str]
    conversation_history: list[dict]


class ConversationAgent:
    """
    Mental health conversation agent using native Llama integration.
    
    Design:
    - Native llama-cpp-python for Q8_0 model fidelity
    - Automatic VRAM optimization with GPU layer calculation
    - Streaming support for "empathic latency" UX
    - Crisis-aware (adjusts tone based on risk level)
    - Traceable conversation flow
    
    UX Strategy:
    - Streaming tokens create "thinking" effect (5-10s feels natural)
    - Higher quality Q8_0 model preserves emotional nuance
    - Graceful CPU fallback if GPU unavailable
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        temperature: Optional[float] = None,
        use_native_llama: bool = True
    ):
        """
        Initialize conversation agent with native Llama support.
        
        Args:
            model_path: Path to GGUF model file (default: from .env LLAMA_MODEL_PATH)
            temperature: Response creativity 0.0-1.0 (default: from .env or 0.7)
            use_native_llama: Use native llama-cpp-python (default: True)
            
        Raises:
            RuntimeError: If model cannot be loaded (Tenet #4: Fail loud, fail early)
        """
        self.temperature = temperature if temperature is not None else float(
            os.getenv("LLAMA_TEMPERATURE", "0.7")
        )
        self.use_native_llama = use_native_llama and LLAMA_CPP_AVAILABLE
        self.is_mock_mode = False
        self.llm = None
        
# ... imports ...
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ConversationAgent:
    """
    Mental health conversation agent using native Llama integration.
    
    Design:
    - Native llama-cpp-python for Q8_0 model fidelity
    - Automatic VRAM optimization with GPU layer calculation
    - Streaming support for "empathic latency" UX
    - Crisis-aware (adjusts tone based on risk level)
    - Traceable conversation flow
    
    UX Strategy:
    - Streaming tokens create "thinking" effect (5-10s feels natural)
    - Higher quality Q8_0 model preserves emotional nuance
    - Graceful CPU fallback if GPU unavailable
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        temperature: Optional[float] = None,
        use_native_llama: bool = True,
        use_rag: bool = True
    ):
        """
        Initialize conversation agent with native Llama support (via Shared Engine).
        
        Args:
            model_path: Ignored (handled by Shared Engine)
            temperature: Response creativity 0.0-1.0 (default: from .env or 0.7)
            use_native_llama: Use native llama-cpp-python (default: True)
            use_rag: Use RAG for prior context retrieval (default: True)
        """
        from src.core.llm_engine import get_llm_engine, LLAMA_AVAILABLE
        
        self.temperature = temperature if temperature is not None else float(
            os.getenv("LLAMA_TEMPERATURE", "0.7")
        )
        self.use_native_llama = use_native_llama and LLAMA_AVAILABLE
        self.is_mock_mode = not LLAMA_AVAILABLE
        self.use_rag = use_rag
        
        # Get Shared Engine
        if self.use_native_llama:
            try:
                self.llm_engine = get_llm_engine()
                # Ensure model is loaded
                if not self.llm_engine.model and not self.llm_engine.mock_mode:
                    self.llm_engine.load_model()
            except Exception as e:
                logger.error("shared_engine_init_failed", error=str(e))
                self.is_mock_mode = True
        else:
            self.llm_engine = None
        
        # Initialize OpenAI if available and key is present
        self.openai_client = None
        openai_key = os.getenv("OPENAI_API_KEY")
        if OPENAI_AVAILABLE and openai_key and openai_key != "not-used":
            try:
                self.openai_client = OpenAI(api_key=openai_key)
                self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
                logger.info("openai_client_initialized", model=self.openai_model)
            except Exception as e:
                logger.warning("openai_initialization_failed", error=str(e))
        
        # Initialize RAG service if enabled
        self.rag_service = None
        if self.use_rag:
            try:
                from src.rag.rag_service import RAGService
                self.rag_service = RAGService()
                logger.info("rag_service_initialized")
            except Exception as e:
                logger.warning("rag_initialization_failed", error=str(e), exc_info=True)
                self.use_rag = False
                
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """
        Build system prompt based on conversation context.
        
        Tenet #8: Engagement Before Intervention
        
        NOTE: Crisis detection is SEPARATE from conversation.
        The agent responds naturally based on conversation history only.
        Crisis alerts happen in parallel, not through the conversation.
        """
        base_prompt = """You are Connor, a supportive mental health AI assistant for high school students.

Your role:
- Listen actively and empathetically
- Validate their feelings without judgment
- Ask open-ended questions to understand better
- Provide gentle encouragement
- Build trust through consistency and continuity

Guidelines:
- Use warm, conversational language (like talking to a friend)
- Reflect their emotions back to them
- Reference previous conversations naturally (e.g., "Last time you mentioned...")
- Never diagnose or prescribe treatment
- Never claim to be a therapist or counselor
- If they seem to need professional help, gently suggest talking to their school counselor

Tone: Warm, supportive, non-judgmental, age-appropriate

Response Length:
- Keep responses CONCISE (1-3 sentences for simple messages)
- Match their energy and detail level
- Don't lecture or over-explain"""
        
        return base_prompt
    
    def _format_chat_messages(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        current_message: str,
        student_id_hash: Optional[str] = None
    ) -> list[dict]:
        """
        Format messages for Llama chat completion with RAG context.
        
        Args:
            system_prompt: System instructions
            conversation_history: Previous messages in current session
            current_message: Current user message
            student_id_hash: Student ID for RAG retrieval
            
        Returns:
            List of message dicts with role and content
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add RAG context if available
        if self.use_rag and self.rag_service and student_id_hash:
            try:
                # Build context from prior sessions
                rag_context = self.rag_service.build_context(
                    current_message=current_message,
                    student_id_hash=student_id_hash,
                    include_conversations=True,
                    include_resources=False,  # Don't include resources in conversation
                    max_context_length=1000
                )
                
                # Format context for LLM
                context_str = self.rag_service.format_context_for_llm(rag_context)
                
                if context_str:
                    # Add as system message with prior context
                    messages.append({
                        "role": "system",
                        "content": f"## Context from Prior Sessions\n\n{context_str}\n\nUse this context naturally in your responses. Reference previous conversations when relevant."
                    })
                    
                    logger.info(
                        "rag_context_added",
                        student_id=student_id_hash,
                        past_conversations=rag_context["retrieval_stats"].get("conversations", {}).get("count", 0)
                    )
            except Exception as e:
                logger.warning("rag_context_retrieval_failed", error=str(e))
        
        # Add conversation history from current session (last 5 messages)
        for msg in conversation_history[-5:]:
            if msg["role"] == "student":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _generate_response_native(
        self,
        messages: list[dict],
        stream: bool = False
    ) -> str | Iterator[str]:
        """
        Generate response using native Llama (via Shared Engine).
        """
        # Stop tokens
        stop_tokens = ["</s>", "[/INST]", "<unk>", "<|endoftext|>", "\n\nUser:", "\n\nHuman:"]
        
        try:
            # Use Shared Engine
            response = self.llm_engine.chat(
                messages=messages,
                stop=stop_tokens,
                temperature=self.temperature,
                max_tokens=512,
                stream=stream
            )
            
            if stream:
                def token_generator():
                    for chunk in response:
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                return token_generator()
            else:
                content = response['choices'][0]['message']['content']
                return sanitize_llm_output(content)
                
        except Exception as e:
            logger.error("native_llama_generation_failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Llama generation failed: {e}") from e
    
    def _generate_response_native_with_tokens(
        self,
        messages: list[dict],
        max_tokens: int,
        stream: bool = False
    ) -> str | Iterator[str]:
        """
        Generate response using native Llama (via Shared Engine) with params.
        """
        stop_tokens = ["</s>", "[/INST]", "<unk>", "<|endoftext|>", "\n\nUser:", "\n\nHuman:"]
        
        try:
            response = self.llm_engine.chat(
                messages=messages,
                stop=stop_tokens,
                temperature=self.temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                def token_generator():
                    for chunk in response:
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                return token_generator()
            else:
                content = response['choices'][0]['message']['content']
                return sanitize_llm_output(content)
                
        except Exception as e:
            logger.error("native_llama_generation_failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Llama generation failed: {e}") from e
    
    async def generate_response(
        self,
        message: str,
        context: ConversationContext,
        max_tokens: Optional[int] = None,
        student_id_hash: Optional[str] = None
    ) -> str:
        """
        Generate response for student message.
        
        IMPORTANT: Crisis detection is SEPARATE from conversation.
        This method generates natural conversational responses based on:
        1. Current message
        2. Conversation history (current session)
        3. Prior session context (via RAG)
        
        Crisis alerts happen in parallel through the safety system.
        
        Args:
            message: Current student message
            context: Conversation context
            max_tokens: Maximum tokens for response
            student_id_hash: Hashed student ID for RAG retrieval
        """
        # Default max_tokens
        if max_tokens is None:
            max_tokens = 512
        
        logger.info(
            "generating_response",
            session_id=context.session_id,
            student_id=student_id_hash,
            use_rag=self.use_rag and student_id_hash is not None,
            openai_available=self.openai_client is not None,
            native_llama_available=self.use_native_llama,
            will_use="native_mistral" if self.use_native_llama else "openai" if self.openai_client else "fallback"
        )
        
        # Build system prompt (no crisis-based modifications)
        system_prompt = self._build_system_prompt(context)
        
        # Format messages with conversation history and RAG context
        messages = self._format_chat_messages(
            system_prompt=system_prompt,
            conversation_history=context.conversation_history,
            current_message=message,
            student_id_hash=student_id_hash
        )
        
        try:
            response_text = ""
            mode = "unknown"
            
            # Prefer Mental Health Mistral if available (better for empathetic responses)
            if self.use_native_llama:
                mode = "native_mistral"
                response_text = self._generate_response_native_with_tokens(
                    messages=messages,
                    max_tokens=max_tokens,
                    stream=False
                )
            
            # Fallback to OpenAI if native not available
            elif self.openai_client:
                mode = "openai"
                completion = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=messages,
                    temperature=self.openai_temperature,
                    max_tokens=max_tokens
                )
                response_text = completion.choices[0].message.content
            
            elif self.is_mock_mode:
                mode = "mock"
                response_text = "I hear you. (Mock response: No models available)"
            
            else:
                mode = "fallback"
                response_text = "I'm having trouble connecting to my brain right now."

            # SAFETY CHECK: Validate response doesn't introduce crisis concepts inappropriately
            response_text = self._validate_response_safety(
                response=response_text,
                student_message=message,
                context=context
            )

            logger.info(
                "response_generated",
                session_id=context.session_id,
                mode=mode
            )
            
            return response_text
            
        except Exception as e:
            logger.error("response_generation_failed", error=str(e), exc_info=True)
            raise RuntimeError(f"Failed to generate response: {e}") from e
    
    def _validate_response_safety(
        self,
        response: str,
        student_message: str,
        context: ConversationContext
    ) -> str:
        """
        Validate that response doesn't introduce crisis concepts inappropriately.
        
        Tenet #1: Safety First - Never plant ideas of self-harm
        
        Args:
            response: Generated response
            student_message: Original student message
            context: Conversation context
            
        Returns:
            Validated (and possibly corrected) response
        """
        # Check if student mentioned suicide/self-harm
        student_mentioned_crisis = any(
            keyword in student_message.lower()
            for keyword in ["suicide", "kill myself", "end my life", "want to die", "hurt myself", "cut myself"]
        )
        
        # Check if response mentions suicide/self-harm
        response_lower = response.lower()
        response_mentions_crisis = any(
            keyword in response_lower
            for keyword in ["suicide", "suicidal", "kill yourself", "end your life", "hurt yourself", "self-harm"]
        )
        
        # CRITICAL: If student didn't mention crisis but response does, this is DANGEROUS
        if response_mentions_crisis and not student_mentioned_crisis:
            logger.critical(
                "response_safety_violation",
                session_id=context.session_id,
                student_message=student_message[:100],
                response_snippet=response[:200],
                reason="response_introduces_crisis_concepts",
                matched_patterns=context.matched_patterns
            )
            
            # Replace with safe, supportive response
            safe_response = self._generate_safe_fallback_response(student_message, context)
            
            logger.warning(
                "response_replaced_for_safety",
                session_id=context.session_id,
                original_length=len(response),
                safe_length=len(safe_response)
            )
            
            return safe_response
        
        return response
    
    def _generate_safe_fallback_response(
        self,
        student_message: str,
        context: ConversationContext
    ) -> str:
        """
        Generate a safe fallback response when primary response is inappropriate.
        
        Tenet #1: Safety First - Hard-coded safe responses
        """
        # Detect the type of stress
        if any(word in student_message.lower() for word in ["exam", "test", "grade", "homework", "assignment"]):
            return (
                "It sounds like you're really stressed about your exam. That's completely understandable - "
                "it's frustrating when things don't go as planned, especially when you've prepared. "
                "Have you thought about how you might talk to your parents about it? "
                "Sometimes it helps to have a plan before the conversation."
            )
        elif any(word in student_message.lower() for word in ["parent", "mom", "dad", "father", "mother"]):
            return (
                "It sounds like you're worried about your parents' reaction. That's a lot of pressure to carry. "
                "It's okay to feel anxious about disappointing them. "
                "If you need someone to talk to about this, your school counselor is a great resource."
            )
        else:
            return (
                "I can hear that you're going through a tough time right now. "
                "It's okay to feel overwhelmed sometimes. "
                "If you'd like to talk more about what's going on, I'm here to listen. "
                "And remember, your school counselor is always available if you need extra support."
            )

