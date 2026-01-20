"""
Dataset Loader for Mental Health Benchmarking

Loads and normalizes various mental health dialogue datasets for evaluation.
Supports: MentalChat16K, EmpatheticDialogues, ESConv, and others.

Usage:
    loader = DatasetLoader()
    dataset = loader.load_mentalchat16k()
    for conversation in dataset:
        # Run safety analysis
        result = safety_service.analyze(conversation['message'])
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import json

try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("Warning: 'datasets' not installed. Install with: pip install datasets")


@dataclass
class ConversationSample:
    """
    Normalized conversation sample across all datasets.
    
    Attributes:
        id: Unique identifier
        message: Student/user message
        context: Previous messages (if available)
        label: Ground truth label (crisis/safe/caution)
        source: Dataset name
        metadata: Additional dataset-specific info
    """
    id: str
    message: str
    context: List[str]
    label: str  # "crisis", "safe", "caution"
    source: str
    metadata: Dict


class DatasetLoader:
    """
    Loads and normalizes mental health dialogue datasets.
    
    Supported Datasets:
    1. MentalChat16K - Mental health counseling QA
    2. EmpatheticDialogues - Empathetic conversations
    3. ESConv - Emotional support conversations
    4. Amod/mental_health_counseling - Real counseling transcripts
    
    Design:
        - Normalizes all datasets to ConversationSample format
        - Handles missing labels gracefully
        - Caches downloaded datasets
        - Provides train/test splits
    """
    
    def __init__(self, cache_dir: str = "evaluation/datasets/.cache"):
        """
        Initialize dataset loader.
        
        Args:
            cache_dir: Directory to cache downloaded datasets
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if not HF_AVAILABLE:
            print("Warning: Hugging Face datasets not available")
            print("Install with: pip install datasets")
    
    def load_mentalchat16k(self, split: str = "train") -> List[ConversationSample]:
        """
        Load MentalChat16K dataset.
        
        Dataset: ~16K mental health counseling QA pairs
        Source: https://huggingface.co/datasets/ShenLab/MentalChat16K
        
        Args:
            split: "train", "validation", or "test"
            
        Returns:
            List of normalized conversation samples
            
        Example:
            loader = DatasetLoader()
            samples = loader.load_mentalchat16k("test")
            print(f"Loaded {len(samples)} samples")
        """
        if not HF_AVAILABLE:
            raise ImportError("datasets library required. Install: pip install datasets")
        
        print(f"Loading MentalChat16K ({split} split)...")
        dataset = load_dataset("ShenLab/MentalChat16K", split=split, cache_dir=str(self.cache_dir))
        
        samples = []
        for idx, item in enumerate(dataset):
            # Extract message and context
            message = item.get('question', item.get('input', ''))
            
            # MentalChat16K doesn't have explicit crisis labels
            # We'll need to infer or use for general evaluation
            sample = ConversationSample(
                id=f"mentalchat_{split}_{idx}",
                message=message,
                context=[],  # MentalChat16K is QA format, no multi-turn context
                label="unknown",  # No explicit crisis labels
                source="MentalChat16K",
                metadata={
                    'response': item.get('answer', item.get('output', '')),
                    'split': split
                }
            )
            samples.append(sample)
        
        print(f"✓ Loaded {len(samples)} samples from MentalChat16K")
        return samples
    
    def load_empathetic_dialogues(self, split: str = "train") -> List[ConversationSample]:
        """
        Load EmpatheticDialogues dataset.
        
        Dataset: ~25K empathetic conversations with emotion labels
        Source: https://huggingface.co/datasets/facebook/empathetic_dialogues
        
        Args:
            split: "train", "validation", or "test"
            
        Returns:
            List of normalized conversation samples
        """
        if not HF_AVAILABLE:
            raise ImportError("datasets library required")
        
        print(f"Loading EmpatheticDialogues ({split} split)...")
        dataset = load_dataset("facebook/empathetic_dialogues", split=split, cache_dir=str(self.cache_dir))
        
        samples = []
        for idx, item in enumerate(dataset):
            # EmpatheticDialogues has emotion labels, not crisis labels
            # We can infer crisis from certain emotions (e.g., "devastated", "terrified")
            emotion = item.get('context', '')
            
            # Map emotions to crisis risk
            crisis_emotions = ['devastated', 'terrified', 'afraid', 'sad', 'lonely']
            label = "caution" if any(e in emotion.lower() for e in crisis_emotions) else "safe"
            
            sample = ConversationSample(
                id=f"empathetic_{split}_{idx}",
                message=item.get('utterance', ''),
                context=item.get('previous_utterances', []),
                label=label,
                source="EmpatheticDialogues",
                metadata={
                    'emotion': emotion,
                    'split': split
                }
            )
            samples.append(sample)
        
        print(f"✓ Loaded {len(samples)} samples from EmpatheticDialogues")
        return samples
    
    def load_custom_crisis_dataset(self, path: str) -> List[ConversationSample]:
        """
        Load custom crisis dataset from JSON file.
        
        Expected format:
        {
            "conversations": [
                {
                    "id": "unique_id",
                    "messages": [{"role": "student", "content": "..."}],
                    "labels": {"is_crisis": true, "risk_level": "CRISIS"}
                }
            ]
        }
        
        Args:
            path: Path to JSON file
            
        Returns:
            List of normalized conversation samples
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset not found: {path}")
        
        print(f"Loading custom dataset from {path}...")
        with open(file_path) as f:
            data = json.load(f)
        
        samples = []
        for conv in data.get('conversations', []):
            # Extract student messages
            messages = [
                msg['content'] for msg in conv['messages']
                if msg['role'] == 'student'
            ]
            
            if not messages:
                continue
            
            # Get labels
            labels = conv.get('labels', {})
            is_crisis = labels.get('is_crisis', False)
            risk_level = labels.get('risk_level', 'SAFE')
            
            # Map to our label format
            if is_crisis or risk_level == 'CRISIS':
                label = "crisis"
            elif risk_level == 'CAUTION':
                label = "caution"
            else:
                label = "safe"
            
            sample = ConversationSample(
                id=conv.get('id', f"custom_{len(samples)}"),
                message=messages[-1],  # Last message
                context=messages[:-1] if len(messages) > 1 else [],
                label=label,
                source="custom",
                metadata=labels
            )
            samples.append(sample)
        
        print(f"✓ Loaded {len(samples)} samples from custom dataset")
        return samples
    
    def load_hard_crisis_dataset(self) -> List[ConversationSample]:
        """
        Load our curated hard crisis dataset.
        
        Returns:
            List of challenging crisis detection cases
        """
        return self.load_custom_crisis_dataset("evaluation/datasets/hard_crisis_dataset.json")


def install_datasets():
    """
    Helper function to install required packages.
    
    Usage:
        python -c "from evaluation.dataset_loader import install_datasets; install_datasets()"
    """
    import subprocess
    import sys
    
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets"])
    print("✓ Installation complete")


if __name__ == "__main__":
    # Test dataset loading
    loader = DatasetLoader()
    
    # Try loading hard crisis dataset
    try:
        samples = loader.load_hard_crisis_dataset()
        print(f"\nHard Crisis Dataset: {len(samples)} samples")
        print(f"Sample: {samples[0].message}")
    except Exception as e:
        print(f"Could not load hard crisis dataset: {e}")
    
    # Try loading MentalChat16K
    if HF_AVAILABLE:
        try:
            samples = loader.load_mentalchat16k("train")
            print(f"\nMentalChat16K: {len(samples)} samples")
        except Exception as e:
            print(f"Could not load MentalChat16K: {e}")
