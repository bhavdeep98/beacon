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
        
        if self.use_native_llama:
            # Native Llama mode
            self.model_path = model_path or os.getenv(
                "LLAMA_MODEL_PATH",
                "models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf"
            )
            
            # Check if model file exists
            if not Path(self.model_path).exists():
                logger.error(
                    "model_file_not_found",
                    model_path=self.model_path,
                    hint="Run tools/download_mistral_model.py to download the model"
                )
                raise RuntimeError(
                    f"Model file not found: {self.model_path}. "
                    "Run tools/download_mistral_model.py to download."
                )
            
            # Calculate optimal GPU layers
            gpu_info = get_gpu_info()
            if gpu_info:
                logger.info("gpu_detected", **gpu_info)
            
            n_gpu_layers = calculate_optimal_layers(
                model_size_gb=7.7,  # Q8_0 Mistral 7B
                total_layers=33,    # Mistral architecture
                safety_buffer_gb=1.5  # KV cache + overhead
            )
            
            # Load model
            try:
                logger.info(
                    "loading_llama_model",
                    model_path=self.model_path,
                    n_gpu_layers=n_gpu_layers,
                    temperature=self.temperature
                )
                
                self.llm = Llama(
                    model_path=self.model_path,
                    n_gpu_layers=n_gpu_layers,
                    n_ctx=4096,  # Context window
                    temperature=self.temperature,
                    verbose=False  # Set to True for debugging
                )
                
                logger.info(
                    "llama_model_loaded",
                    model_path=self.model_path,
                    n_gpu_layers=n_gpu_layers,
                    mode="native"
                )
                
            except Exception as e:
                logger.error(
                    "llama_model_load_failed",
                    model_path=self.model_path,
                    error=str(e),
                    exc_info=True
                )
                raise RuntimeError(f"Failed to load Llama model: {e}") from e
        else:
            # Fallback to mock mode if native Llama not available
            logger.warning(
                "native_llama_unavailable_using_mock",
                reason="llama-cpp-python not installed or disabled"
            )
            self.is_mock_mode = True
    
    def _build_system_prompt(self, context: ConversationContext) -> str:
        """
        Build system prompt based on conversation context.
        
        Tenet #8: Engagement Before Intervention
        """
        base_prompt = """You are Connor, a supportive mental health AI assistant for high school students.

Your role:
- Listen actively and empathetically
- Validate their feelings without judgment
- Ask open-ended questions to understand better
- Provide gentle encouragement
- Build trust through consistency

Guidelines:
- Use warm, conversational language (like talking to a friend)
- Keep responses concise (2-3 sentences)
- Reflect their emotions back to them
- Never diagnose or prescribe treatment
- Never claim to be a therapist or counselor
- If they need professional help, encourage them to talk to their school counselor

Tone: Warm, supportive, non-judgmental, age-appropriate"""
        
        # Adjust based on risk level
        if context.risk_level == "CAUTION":
            base_prompt += """

IMPORTANT: This student is showing some concerning signs. Be extra attentive:
- Gently explore what's troubling them
- Validate their struggles
- Subtly encourage them to reach out to their counselor
- Watch for escalation"""
        
        return base_prompt
    
    def _format_chat_messages(
        self,
        system_prompt: str,
        conversation_history: list[dict],
        current_message: str
    ) -> list[dict]:
        """
        Format messages for Llama chat completion.
        
        Args:
            system_prompt: System instructions
            conversation_history: Previous messages
            current_message: Current user message
            
        Returns:
            List of message dicts with role and content
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (last 5 messages)
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
        Generate response using native Llama.
        
        Args:
            messages: Chat messages
            stream: Whether to stream tokens (for UX)
            
        Returns:
            Generated response text or iterator of tokens
        """
        # Stop tokens to prevent "alphabet soup"
        stop_tokens = ["</s>", "[/INST]", "<unk>", "<|endoftext|>", "\n\nUser:", "\n\nHuman:"]
        
        try:
            response = self.llm.create_chat_completion(
                messages=messages,
                stop=stop_tokens,
                temperature=self.temperature,
                max_tokens=512,  # Concise responses (2-3 sentences)
                stream=stream
            )
            
            if stream:
                # Return generator for streaming
                def token_generator():
                    for chunk in response:
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                
                return token_generator()
            else:
                # Return complete response
                content = response['choices'][0]['message']['content']
                return sanitize_llm_output(content)
                
        except Exception as e:
            logger.error(
                "native_llama_generation_failed",
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Llama generation failed: {e}") from e
    
    async def generate_response(
        self,
        message: str,
        context: ConversationContext
    ) -> str:
        """
        Generate response for student message.
        
        Args:
            message: Student's message
            context: Conversation context with risk assessment
            
        Returns:
            AI-generated response
            
        Raises:
            RuntimeError: If response generation fails
        """
        # Check for crisis override first
        if context.risk_level == "CRISIS":
            # Tenet #1: Hard-coded crisis protocol
            crisis_message = (
                "I'm really concerned about what you've shared. "
                "Your safety is the most important thing right now. "
                "I've notified your school counselor, and they'll reach out soon.\n\n"
                "In the meantime, here are some resources:\n\n"
                "🆘 National Suicide Prevention Lifeline: 988\n"
                "💬 Crisis Text Line: Text HOME to 741741\n"
                "🌐 Online Chat: https://suicidepreventionlifeline.org/chat/\n\n"
                "You're not alone in this. Help is available 24/7."
            )
            
            logger.warning(
                "crisis_override_triggered",
                session_id=context.session_id,
                risk_score=context.risk_score,
                matched_patterns=context.matched_patterns
            )
            
            return crisis_message
        
        # Build system prompt
        system_prompt = self._build_system_prompt(context)
        
        # Format messages
        messages = self._format_chat_messages(
            system_prompt=system_prompt,
            conversation_history=context.conversation_history,
            current_message=message
        )
        
        # Generate response
        try:
            if self.is_mock_mode:
                response_text = "I hear you. (Mock response: Llama model not available)"
            elif self.use_native_llama:
                # Native Llama generation
                response_text = self._generate_response_native(
                    messages=messages,
                    stream=False  # Set to True for streaming in future
                )
            else:
                # Should not reach here, but fallback to mock
                response_text = "I hear you. (Fallback response)"
            
            logger.info(
                "response_generated",
                session_id=context.session_id,
                risk_level=context.risk_level,
                response_length=len(response_text),
                mode="native_llama" if self.use_native_llama else "mock"
            )
            
            return response_text
            
        except Exception as e:
            logger.error(
                "response_generation_failed",
                session_id=context.session_id,
                error=str(e),
                exc_info=True
            )
            # Tenet #4: Fail loud, fail early
            raise RuntimeError(f"Failed to generate response: {e}") from e

