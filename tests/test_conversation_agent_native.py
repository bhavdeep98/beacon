"""
Tests for Native Llama Conversation Agent

Tenet #1: Safety First - Verify crisis override works
Tenet #3: Explicit Over Clever - Clear test cases
Tenet #4: Fail Loud, Fail Early - Test error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from conversation import ConversationAgent, ConversationContext


class TestConversationAgentNative:
    """Test native Llama conversation agent."""
    
    @patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', False)
    def test_init_mock_mode_when_llama_unavailable(self):
        """Test agent falls back to mock mode when llama-cpp-python unavailable."""
        agent = ConversationAgent()
        
        assert agent.is_mock_mode is True
        assert agent.llm is None
    
    @patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', True)
    @patch('conversation.conversation_agent.Path')
    def test_init_fails_when_model_not_found(self, mock_path):
        """Test agent fails loud when model file not found."""
        # Mock model file doesn't exist
        mock_path.return_value.exists.return_value = False
        
        with pytest.raises(RuntimeError, match="Model file not found"):
            ConversationAgent()
    
    @pytest.mark.asyncio
    async def test_crisis_override_bypasses_llm(self):
        """Test crisis messages trigger hard-coded response (Tenet #1)."""
        # Create agent in mock mode
        with patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', False):
            agent = ConversationAgent()
        
        # Create crisis context
        context = ConversationContext(
            session_id="test_session",
            risk_level="CRISIS",
            risk_score=0.95,
            matched_patterns=["suicidal_ideation"],
            conversation_history=[]
        )
        
        # Generate response
        response = await agent.generate_response(
            message="I want to die",
            context=context
        )
        
        # Verify crisis protocol triggered
        assert "988" in response  # Suicide prevention lifeline
        assert "Crisis Text Line" in response
        assert "counselor" in response.lower()
    
    @pytest.mark.asyncio
    async def test_safe_message_generates_response(self):
        """Test safe messages generate empathetic response."""
        # Create agent in mock mode
        with patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', False):
            agent = ConversationAgent()
        
        # Create safe context
        context = ConversationContext(
            session_id="test_session",
            risk_level="SAFE",
            risk_score=0.1,
            matched_patterns=[],
            conversation_history=[]
        )
        
        # Generate response
        response = await agent.generate_response(
            message="I'm feeling stressed about exams",
            context=context
        )
        
        # Verify response generated (mock mode)
        assert "Mock response" in response or len(response) > 0
    
    @pytest.mark.asyncio
    async def test_caution_message_adjusts_system_prompt(self):
        """Test CAUTION risk level adjusts system prompt."""
        # Create agent in mock mode
        with patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', False):
            agent = ConversationAgent()
        
        # Create caution context
        context = ConversationContext(
            session_id="test_session",
            risk_level="CAUTION",
            risk_score=0.65,
            matched_patterns=["anxiety_symptoms"],
            conversation_history=[]
        )
        
        # Build system prompt
        system_prompt = agent._build_system_prompt(context)
        
        # Verify prompt includes caution guidance
        assert "concerning signs" in system_prompt.lower()
        assert "extra attentive" in system_prompt.lower()
    
    def test_format_chat_messages(self):
        """Test message formatting for Llama."""
        # Create agent in mock mode
        with patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', False):
            agent = ConversationAgent()
        
        # Create conversation history
        history = [
            {"role": "student", "content": "I'm stressed"},
            {"role": "assistant", "content": "I hear you"},
            {"role": "student", "content": "It's getting worse"}
        ]
        
        # Format messages
        messages = agent._format_chat_messages(
            system_prompt="You are Connor",
            conversation_history=history,
            current_message="I need help"
        )
        
        # Verify format
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are Connor"
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "I need help"
        assert len(messages) == 5  # system + 3 history + current
    
    def test_sanitize_llm_output(self):
        """Test LLM output sanitization removes artifacts."""
        from conversation.conversation_agent import sanitize_llm_output
        
        # Test removing common artifacts
        dirty_text = "Hello <unk> world </s> test"
        clean_text = sanitize_llm_output(dirty_text)
        
        assert "<unk>" not in clean_text
        assert "</s>" not in clean_text
        assert "Hello" in clean_text
        assert "world" in clean_text
    
    @pytest.mark.asyncio
    async def test_generation_failure_raises_error(self):
        """Test generation failures raise RuntimeError (Tenet #4)."""
        # Create agent in mock mode
        with patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', False):
            agent = ConversationAgent()
        
        # Mock generation to fail
        with patch.object(agent, '_generate_response_native', side_effect=Exception("LLM error")):
            agent.use_native_llama = True  # Force native mode
            
            context = ConversationContext(
                session_id="test_session",
                risk_level="SAFE",
                risk_score=0.1,
                matched_patterns=[],
                conversation_history=[]
            )
            
            # Should raise RuntimeError
            with pytest.raises(RuntimeError, match="Failed to generate response"):
                await agent.generate_response(
                    message="Test message",
                    context=context
                )


class TestNativeLlamaGeneration:
    """Test native Llama generation (requires model)."""
    
    @pytest.mark.skipif(
        not Path("models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf").exists(),
        reason="Model file not available"
    )
    @patch('conversation.conversation_agent.LLAMA_CPP_AVAILABLE', True)
    def test_native_generation_with_real_model(self):
        """Integration test with real model (skipped if model not available)."""
        # This test requires the actual model file
        # Run only when model is downloaded
        agent = ConversationAgent()
        
        assert agent.use_native_llama is True
        assert agent.llm is not None
        
        # Test generation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"}
        ]
        
        response = agent._generate_response_native(messages, stream=False)
        
        assert isinstance(response, str)
        assert len(response) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
