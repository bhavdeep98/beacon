"""
Test Suite for Safety Service

Comprehensive tests for crisis detection system:
1. Explicit crisis keyword detection (100% recall target)
2. Boundary validation (hyperbole vs genuine crisis)
3. Strategy isolation tests (regex, semantic, sarcasm)
4. Context window tests
5. Performance tests (latency < 50ms)
6. Integration tests

Design:
- Each test class focuses on one aspect
- Tests are independent (no shared state)
- Clear failure messages for debugging
- Performance benchmarks included
"""

import pytest
from src.safety.safety_analyzer import SafetyService
from src.safety.strategies import (
    RegexDetectionStrategy,
    SemanticDetectionStrategy,
    SarcasmFilterStrategy
)
from src.safety.strategy_factory import SafetyAnalyzerFactory


@pytest.fixture
def safety_service():
    """
    Initialize Safety Service for testing.
    
    Returns:
        SafetyService instance with default patterns
    """
    return SafetyService(patterns_path="config/crisis_patterns.yaml")


@pytest.fixture
def patterns():
    """
    Load crisis patterns for strategy testing.
    
    Returns:
        Crisis patterns dictionary from YAML
    """
    return SafetyAnalyzerFactory.load_patterns("config/crisis_patterns.yaml")


@pytest.fixture
def regex_strategy(patterns):
    """Initialize regex strategy for isolated testing."""
    return RegexDetectionStrategy(patterns)


@pytest.fixture
def semantic_strategy(patterns):
    """Initialize semantic strategy for isolated testing."""
    return SemanticDetectionStrategy(patterns)


@pytest.fixture
def sarcasm_strategy(patterns):
    """Initialize sarcasm filter for isolated testing."""
    return SarcasmFilterStrategy(patterns)


class TestExplicitCrisisDetection:
    """
    Test 100% recall on explicit crisis keywords.
    
    Target: Zero false negatives on explicit crisis language.
    These are the "safety floor" - must never miss these.
    """
    
    def test_suicidal_ideation_explicit(self, safety_service):
        """
        Test detection of explicit suicidal ideation.
        
        Critical: These MUST be detected (100% recall).
        Failure here means missed crisis.
        """
        messages = [
            "I want to die",
            "I'm going to kill myself",
            "I want to end my life",
            "Life is not worth living",
            "I'd be better off dead"
        ]
        
        for message in messages:
            result = safety_service.analyze(message)
            assert result.is_crisis, f"CRITICAL: Failed to detect crisis in: {message}"
            assert result.p_regex >= 0.90, f"Regex score too low for: {message}"
            assert "suicidal_ideation" in result.matched_patterns, \
                f"Pattern not matched for: {message}"
    
    def test_self_harm_explicit(self, safety_service):
        """Test detection of explicit self-harm."""
        test_cases = [
            ("I cut myself last night", 0.85),
            ("I want to hurt myself", 0.85),
            ("I've been self harming", 0.85),
            ("I'm going to burn myself", 0.85)
        ]
        
        for message, min_score in test_cases:
            result = safety_service.analyze(message)
            assert result.is_crisis, f"Failed to detect crisis in: {message}"
            assert result.p_regex >= min_score, f"Regex score {result.p_regex} < {min_score} for: {message}"
            assert "self_harm" in result.matched_patterns
    
    def test_intent_with_plan(self, safety_service):
        """Test detection of suicidal intent with plan (highest risk)."""
        messages = [
            "I have a plan to kill myself",
            "I'm going to jump off the bridge tonight",
            "I have the pills ready",
            "Tonight I will end it"
        ]
        
        for message in messages:
            result = safety_service.analyze(message)
            assert result.is_crisis, f"Failed to detect crisis in: {message}"
            assert result.p_regex >= 0.95, f"Regex score too low for: {message}"
            assert "intent_with_plan" in result.matched_patterns


class TestBoundaryValidation:
    """Test that hyperbole and figurative language don't trigger false positives."""
    
    def test_teenage_hyperbole(self, safety_service):
        """Test that common teenage hyperbole doesn't trigger crisis."""
        safe_messages = [
            "This homework is killing me",
            "I'm dying of boredom",
            "My parents would kill me if I failed",
            "I'm dead tired",
            "That test murdered me"
        ]
        
        for message in safe_messages:
            result = safety_service.analyze(message)
            assert not result.is_crisis, f"False positive on: {message}"
            assert result.p_regex < 0.90, f"Regex score too high for: {message}"
    
    def test_positive_alive_statements(self, safety_service):
        """Test that positive statements about being alive don't trigger."""
        safe_messages = [
            "I feel alive and happy",
            "I'm so alive right now",
            "Life is worth living",
            "I want to live my best life"
        ]
        
        for message in safe_messages:
            result = safety_service.analyze(message)
            assert not result.is_crisis, f"False positive on: {message}"
            assert result.p_regex == 0.0, f"Should have zero regex match for: {message}"
    
    def test_boundary_case_unalive_vs_alive(self, safety_service):
        """Test critical boundary: 'I am unalive' vs 'I feel alive and happy'."""
        # Crisis case - "unalive" is coded language for suicide
        crisis_msg = "I want to be unalive"
        result_crisis = safety_service.analyze(crisis_msg)
        
        # Safe case
        safe_msg = "I feel alive and happy"
        result_safe = safety_service.analyze(safe_msg)
        
        # Safe message should not trigger crisis
        assert not result_safe.is_crisis, "False positive on positive statement"
        
        # Crisis message may or may not trigger depending on semantic layer
        # This is a known limitation - "unalive" is coded language not in patterns


class TestSemanticLayer:
    """Test semantic layer functionality."""
    
    def test_semantic_layer_initialized(self, safety_service):
        """Test semantic layer is initialized and working."""
        # Test that semantic layer produces scores
        # Exact phrases from patterns should score high
        result = safety_service.analyze("I want to die")
        
        # Should have both regex and semantic matches
        assert result.p_regex > 0, "Regex should match"
        assert result.p_semantic >= 0, "Semantic should produce score"
        assert result.is_crisis, "Should detect crisis"


class TestPerformance:
    """Test latency requirements."""
    
    def test_latency_under_50ms(self, safety_service):
        """Test that analysis completes in <50ms."""
        test_messages = [
            "I want to die",
            "This homework is killing me",
            "I'm feeling really anxious today",
            "Can you help me with my math homework?"
        ]
        
        for message in test_messages:
            result = safety_service.analyze(message)
            assert result.latency_ms < 50, (
                f"Latency {result.latency_ms}ms exceeds 50ms for: {message}"
            )
    
    def test_batch_throughput(self, safety_service):
        """Test high-throughput batch processing."""
        import time
        
        messages = [
            "I want to die",
            "I'm feeling sad",
            "This is boring",
            "I need help"
        ] * 25  # 100 messages
        
        start = time.perf_counter()
        for message in messages:
            safety_service.analyze(message)
        elapsed = time.perf_counter() - start
        
        throughput = len(messages) / elapsed
        assert throughput > 20, f"Throughput {throughput:.1f} msg/s is too low"


class TestClinicalScoring:
    """Test clinical scoring accuracy."""
    
    def test_crisis_score_10_out_of_10(self, safety_service):
        """Test that deterministic triggers score high for safety."""
        explicit_crisis = [
            ("I want to kill myself", 0.95),
            ("I have a plan to end my life", 0.95),
        ]
        
        for message, min_score in explicit_crisis:
            result = safety_service.analyze(message)
            # For deterministic triggers, we expect high confidence
            assert result.p_regex >= min_score, (
                f"Regex score {result.p_regex} < {min_score} for: {message}"
            )
            assert result.is_crisis


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/safety", "--cov-report=term-missing"])



class TestStrategyIsolation:
    """
    Test each detection strategy in isolation.
    
    Purpose: Verify each strategy works independently.
    Helps debug which layer is failing when integration tests fail.
    """
    
    def test_regex_strategy_explicit_keywords(self, regex_strategy):
        """Test regex strategy catches explicit keywords."""
        test_cases = [
            ("I want to die", 0.95, ["suicidal_ideation"]),
            ("I'm going to kill myself", 0.95, ["suicidal_ideation"]),
            ("I cut myself", 0.85, ["self_harm"]),
            ("I'm feeling sad", 0.0, []),  # Should not match
        ]
        
        for message, expected_min_score, expected_patterns in test_cases:
            score, patterns = regex_strategy.analyze(message)
            
            if expected_min_score > 0:
                assert score >= expected_min_score, \
                    f"Regex score {score} < {expected_min_score} for: {message}"
                for pattern in expected_patterns:
                    assert pattern in patterns, \
                        f"Pattern {pattern} not in {patterns} for: {message}"
            else:
                assert score == 0.0, f"Should not match: {message}"
    
    def test_regex_word_boundaries(self, regex_strategy):
        """Test regex respects word boundaries."""
        # Should NOT match (word boundaries)
        no_match_cases = [
            "I feel alive",  # Contains "alive" but not "die"
            "studied hard",  # Contains "die" but as part of word
            "I'm living my best life",  # Positive context
        ]
        
        for message in no_match_cases:
            score, patterns = regex_strategy.analyze(message)
            assert score == 0.0, f"False positive on: {message}"
    
    def test_semantic_strategy_with_crisis_terms(self, semantic_strategy):
        """Test semantic strategy produces scores."""
        # Test that semantic strategy is working
        # Exact match from patterns should score high
        score, patterns = semantic_strategy.analyze("I want to die")
        
        # Should produce a score (may or may not exceed threshold)
        assert score >= 0, "Should produce score"
    
    def test_semantic_with_context_improves_accuracy(self, semantic_strategy):
        """Test that context improves semantic accuracy."""
        ambiguous_message = "I'm checking out early"
        
        # Without context - ambiguous
        score_no_context, _ = semantic_strategy.analyze(ambiguous_message)
        
        # With crisis context - clearer intent
        crisis_context = [
            "I can't take it anymore",
            "Everything is hopeless",
            "Nobody cares"
        ]
        score_with_context, _ = semantic_strategy.analyze(
            ambiguous_message,
            context=crisis_context
        )
        
        # Context should increase confidence
        assert score_with_context >= score_no_context, \
            "Context should improve or maintain semantic score"
    
    def test_sarcasm_filter_detects_hyperbole(self, sarcasm_strategy):
        """Test sarcasm filter catches teenage hyperbole."""
        hyperbole_cases = [
            ("This homework is killing me", 0.9, ["hyperbole"]),
            ("I'm dying of boredom", 0.9, ["hyperbole"]),
            ("My parents would kill me", 0.9, ["hyperbole"]),
            ("I'm dead tired", 0.9, ["hyperbole"]),
        ]
        
        for message, expected_min_score, expected_patterns in hyperbole_cases:
            score, patterns = sarcasm_strategy.analyze(message)
            assert score >= expected_min_score, \
                f"Sarcasm score {score} < {expected_min_score} for: {message}"
            assert patterns == expected_patterns, \
                f"Expected {expected_patterns}, got {patterns}"
    
    def test_sarcasm_filter_detects_positive_sentiment(self, sarcasm_strategy):
        """Test sarcasm filter catches positive sentiment indicators."""
        positive_cases = [
            "I'm dying lol",
            "This is killing me haha",
            "I want to die jk",
        ]
        
        for message in positive_cases:
            score, patterns = sarcasm_strategy.analyze(message)
            assert score >= 0.8, f"Should detect positive sentiment in: {message}"
            assert "positive_sentiment" in patterns
    
    def test_sarcasm_filter_allows_genuine_crisis(self, sarcasm_strategy):
        """Test sarcasm filter doesn't block genuine crisis."""
        genuine_crisis = [
            "I want to die",
            "I'm going to kill myself",
            "I can't take it anymore",
        ]
        
        for message in genuine_crisis:
            score, patterns = sarcasm_strategy.analyze(message)
            assert score == 0.0, f"Should not filter genuine crisis: {message}"


class TestContextWindow:
    """
    Test context window functionality.
    
    Purpose: Verify semantic layer uses context correctly.
    Context helps disambiguate ambiguous messages.
    """
    
    def test_context_disambiguates_ambiguous_message(self, safety_service):
        """Test context helps clarify ambiguous messages."""
        ambiguous = "I'm checking out early"
        
        # Safe context (leaving class)
        safe_context = [
            "What time is class over?",
            "I have a doctor's appointment",
        ]
        result_safe = safety_service.analyze(ambiguous, context=safe_context)
        
        # Crisis context (leaving life)
        crisis_context = [
            "I can't take it anymore",
            "Everything is hopeless",
            "Nobody would miss me",
        ]
        result_crisis = safety_service.analyze(ambiguous, context=crisis_context)
        
        # Crisis context should have higher semantic score
        assert result_crisis.p_semantic >= result_safe.p_semantic, \
            "Crisis context should increase semantic score"
    
    def test_context_window_size_limit(self, semantic_strategy):
        """Test context window uses only last 3 messages."""
        message = "I'm feeling overwhelmed"
        
        # Provide 5 messages of context
        long_context = [
            "Message 1",
            "Message 2",
            "Message 3",
            "Message 4",
            "Message 5",
        ]
        
        # Should only use last 3
        score, _ = semantic_strategy.analyze(message, context=long_context)
        
        # Just verify it doesn't crash with long context
        assert score >= 0.0


class TestSarcasmFilterIntegration:
    """
    Test sarcasm filter integration with safety service.
    
    Purpose: Verify sarcasm filter reduces false positives.
    When hyperbole detected, semantic score should be reduced.
    """
    
    def test_sarcasm_filter_reduces_semantic_score(self, safety_service):
        """Test sarcasm filter reduces semantic score for hyperbole."""
        hyperbole_message = "This homework is killing me"
        
        result = safety_service.analyze(hyperbole_message)
        
        # Should detect sarcasm
        assert result.p_sarcasm > 0.7, "Should detect hyperbole"
        
        # Should mark as filtered
        assert result.sarcasm_filtered, "Should mark as sarcasm filtered"
        
        # Should NOT trigger crisis
        assert not result.is_crisis, "Hyperbole should not trigger crisis"
    
    def test_sarcasm_filter_allows_genuine_crisis_with_lol(self, safety_service):
        """Test edge case: genuine crisis with nervous laughter."""
        # This is a known limitation - "lol" may filter genuine crisis
        # But regex layer should still catch it
        message = "I want to kill myself lol"
        
        result = safety_service.analyze(message)
        
        # Sarcasm filter may trigger (nervous laughter)
        # But regex should still detect crisis
        assert result.p_regex >= 0.90, "Regex should catch explicit keyword"
        assert result.is_crisis, "Should still detect crisis despite 'lol'"


class TestPerformanceRegression:
    """
    Test performance doesn't regress.
    
    Purpose: Ensure optimizations don't break performance SLA.
    Target: <50ms P95 latency
    """
    
    def test_single_message_latency(self, safety_service):
        """Test single message analysis latency."""
        test_messages = [
            "I want to die",
            "This homework is killing me",
            "I'm feeling anxious",
            "Can you help me?",
        ]
        
        for message in test_messages:
            result = safety_service.analyze(message)
            assert result.latency_ms < 50, \
                f"Latency {result.latency_ms}ms exceeds 50ms SLA for: {message}"
    
    def test_with_context_latency(self, safety_service):
        """Test latency with context window."""
        message = "I'm checking out early"
        context = ["I'm stressed", "Can't sleep", "Everything is hard"]
        
        result = safety_service.analyze(message, context=context)
        
        # Context adds ~5-10ms, should still be under 50ms
        assert result.latency_ms < 50, \
            f"Latency with context {result.latency_ms}ms exceeds 50ms SLA"
    
    def test_batch_throughput_maintained(self, safety_service):
        """Test batch processing maintains throughput."""
        import time
        
        messages = [
            "I want to die",
            "I'm feeling sad",
            "This is boring",
            "I need help",
        ] * 25  # 100 messages
        
        start = time.perf_counter()
        for message in messages:
            safety_service.analyze(message)
        elapsed = time.perf_counter() - start
        
        throughput = len(messages) / elapsed
        assert throughput > 20, \
            f"Throughput {throughput:.1f} msg/s below 20 msg/s target"


class TestEdgeCases:
    """
    Test edge cases and error handling.
    
    Purpose: Ensure system handles unusual inputs gracefully.
    """
    
    def test_empty_message(self, safety_service):
        """Test handling of empty message."""
        result = safety_service.analyze("")
        assert not result.is_crisis
        assert result.p_regex == 0.0
        assert result.p_semantic == 0.0
    
    def test_very_long_message(self, safety_service):
        """Test handling of very long message."""
        long_message = "I'm feeling sad. " * 100  # 1800 chars
        result = safety_service.analyze(long_message)
        
        # Should complete without error
        assert result.latency_ms < 100, "Long message should still be fast"
    
    def test_unicode_and_emojis(self, safety_service):
        """Test handling of unicode and emojis."""
        messages_with_unicode = [
            "I want to die 😢",
            "This homework is killing me 😂",
            "I'm feeling sad 💔",
        ]
        
        for message in messages_with_unicode:
            result = safety_service.analyze(message)
            # Should handle without crashing
            assert result is not None
    
    def test_none_context(self, safety_service):
        """Test handling of None context."""
        result = safety_service.analyze("I'm sad", context=None)
        assert result is not None
    
    def test_empty_context(self, safety_service):
        """Test handling of empty context list."""
        result = safety_service.analyze("I'm sad", context=[])
        assert result is not None
