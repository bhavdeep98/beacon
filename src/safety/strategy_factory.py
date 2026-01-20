"""
Safety Analyzer Factory

Creates and configures detection strategies for crisis analysis.
Centralizes strategy instantiation and pattern loading.

Factory Method Pattern:
- Loads crisis patterns from YAML configuration
- Creates appropriate detection strategies (Regex, Semantic, Sarcasm)
- Validates configuration before strategy creation
- Provides single point of strategy management

Usage:
    strategies = SafetyAnalyzerFactory.create_all_strategies("config/crisis_patterns.yaml")
    service = SafetyService(strategies)
"""

from typing import List
from pathlib import Path
import yaml
import structlog

from .strategies import (
    DetectionStrategy,
    RegexDetectionStrategy,
    SemanticDetectionStrategy,
    SarcasmFilterStrategy
)

logger = structlog.get_logger()


class SafetyAnalyzerFactory:
    """
    Factory for creating crisis detection strategies.
    
    Responsibilities:
    - Load crisis patterns from YAML configuration
    - Create detection strategy instances
    - Validate configuration structure
    - Provide centralized strategy management
    
    Design Pattern: Factory Method
    
    Example:
        # Create all strategies
        strategies = SafetyAnalyzerFactory.create_all_strategies(
            "config/crisis_patterns.yaml"
        )
        
        # Create individual strategy
        patterns = SafetyAnalyzerFactory.load_patterns("config/crisis_patterns.yaml")
        regex_strategy = SafetyAnalyzerFactory.create_regex_strategy(patterns)
    """
    
    @staticmethod
    def load_patterns(patterns_path: str) -> dict:
        """
        Load crisis patterns from YAML configuration file.
        
        Validates that the YAML file exists and contains required structure.
        
        Args:
            patterns_path: Path to crisis patterns YAML file
                          (e.g., "config/crisis_patterns.yaml")
            
        Returns:
            Dictionary containing crisis patterns with structure:
            {
                'crisis_keywords': {
                    'category_name': {
                        'patterns': ['phrase1', 'phrase2'],
                        'confidence': 0.95
                    }
                }
            }
            
        Raises:
            FileNotFoundError: If patterns file doesn't exist at specified path
            ValueError: If patterns file missing 'crisis_keywords' key
            
        Example:
            patterns = SafetyAnalyzerFactory.load_patterns(
                "config/crisis_patterns.yaml"
            )
            # patterns['crisis_keywords']['suicidal_ideation']['confidence'] == 0.95
        """
        patterns_file = Path(patterns_path)
        
        if not patterns_file.exists():
            raise FileNotFoundError(f"Crisis patterns file not found: {patterns_path}")
        
        with open(patterns_file) as f:
            patterns = yaml.safe_load(f)
        
        # Validate structure
        if 'crisis_keywords' not in patterns:
            raise ValueError("Invalid patterns file: missing 'crisis_keywords'")
        
        logger.info(
            "patterns_loaded",
            path=patterns_path,
            categories=len(patterns['crisis_keywords'])
        )
        
        return patterns
    
    @staticmethod
    def create_regex_strategy(patterns: dict) -> RegexDetectionStrategy:
        """
        Create deterministic regex-based detection strategy.
        
        This strategy uses RE2 regex engine for exact keyword matching.
        Provides the "safety floor" - guaranteed to catch explicit crisis language.
        
        Args:
            patterns: Crisis patterns dictionary from load_patterns()
            
        Returns:
            Configured RegexDetectionStrategy instance
            
        Example:
            patterns = SafetyAnalyzerFactory.load_patterns("config/crisis_patterns.yaml")
            regex = SafetyAnalyzerFactory.create_regex_strategy(patterns)
            score, matches = regex.analyze("I want to die")
            # score == 0.95, matches == ['suicidal_ideation']
        """
        return RegexDetectionStrategy(patterns)
    
    @staticmethod
    def create_semantic_strategy(
        patterns: dict,
        model_name: str = 'all-MiniLM-L6-v2'
    ) -> SemanticDetectionStrategy:
        """
        Create semantic embedding-based detection strategy.
        
        This strategy uses sentence transformers to catch obfuscated or
        coded language that doesn't match explicit keywords.
        Examples: "checking out early", "time to disappear"
        
        Args:
            patterns: Crisis patterns dictionary from load_patterns()
            model_name: Sentence transformer model name
                       Default: 'all-MiniLM-L6-v2' (384-dim embeddings)
            
        Returns:
            Configured SemanticDetectionStrategy instance
            
        Note:
            Model is downloaded on first use (~80MB).
            Pre-computes embeddings for all crisis phrases at initialization.
            
        Example:
            patterns = SafetyAnalyzerFactory.load_patterns("config/crisis_patterns.yaml")
            semantic = SafetyAnalyzerFactory.create_semantic_strategy(patterns)
            score, matches = semantic.analyze("I'm checking out early")
            # score > 0.7 (catches obfuscated language)
        """
        return SemanticDetectionStrategy(patterns, model_name)
    
    @staticmethod
    def create_sarcasm_filter(patterns: dict) -> SarcasmFilterStrategy:
        """
        Create sarcasm and hyperbole detection strategy.
        
        This strategy filters out teenage hyperbole and figurative language
        to reduce false positives from the semantic layer.
        Examples: "homework is killing me", "dying of boredom"
        
        Args:
            patterns: Crisis patterns dictionary (for reference)
            
        Returns:
            Configured SarcasmFilterStrategy instance
            
        Note:
            When sarcasm detected (score > 0.7), semantic scores are
            reduced by 90% to prevent false crisis triggers.
            
        Example:
            patterns = SafetyAnalyzerFactory.load_patterns("config/crisis_patterns.yaml")
            sarcasm = SafetyAnalyzerFactory.create_sarcasm_filter(patterns)
            score, matches = sarcasm.analyze("This homework is killing me")
            # score == 0.9, matches == ['hyperbole']
        """
        return SarcasmFilterStrategy(patterns)
    
    @staticmethod
    def create_all_strategies(patterns_path: str) -> List[DetectionStrategy]:
        """
        Create all available detection strategies in one call.
        
        Convenience method that loads patterns and creates all strategies:
        1. RegexDetectionStrategy (deterministic keyword matching)
        2. SemanticDetectionStrategy (embedding similarity)
        3. SarcasmFilterStrategy (hyperbole detection)
        
        Args:
            patterns_path: Path to crisis patterns YAML file
            
        Returns:
            List of configured detection strategy instances
            
        Raises:
            FileNotFoundError: If patterns file doesn't exist
            ValueError: If patterns file is invalid
            
        Example:
            strategies = SafetyAnalyzerFactory.create_all_strategies(
                "config/crisis_patterns.yaml"
            )
            # strategies[0] = RegexDetectionStrategy
            # strategies[1] = SemanticDetectionStrategy
            # strategies[2] = SarcasmFilterStrategy
            
            for strategy in strategies:
                score, matches = strategy.analyze("student message")
        """
        patterns = SafetyAnalyzerFactory.load_patterns(patterns_path)
        
        strategies = [
            SafetyAnalyzerFactory.create_regex_strategy(patterns),
            SafetyAnalyzerFactory.create_semantic_strategy(patterns),
            SafetyAnalyzerFactory.create_sarcasm_filter(patterns)
        ]
        
        logger.info(
            "strategies_created",
            count=len(strategies),
            types=[s.get_name() for s in strategies]
        )
        
        return strategies
