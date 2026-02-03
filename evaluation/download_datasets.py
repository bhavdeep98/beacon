#!/usr/bin/env python3
"""
Download and prepare evaluation datasets.

Downloads:
1. MentalChat16K - Primary mental health counseling dataset
2. EmpatheticDialogues - Empathetic conversations
3. Amod/mental_health_counseling - Real counseling transcripts

Extracts safety-critical subset for Milestone 1 evaluation.
"""

import sys
from pathlib import Path
import json
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.dataset_loader import DatasetLoader, ConversationSample
import structlog

logger = structlog.get_logger()


def extract_safety_critical_subset(
    samples: List[ConversationSample],
    min_samples: int = 500
) -> List[Dict]:
    """
    Extract safety-critical subset with explicit crisis markers.
    
    Filters for messages containing crisis keywords to create
    a focused test set for deterministic safety floor validation.
    
    Args:
        samples: All conversation samples
        min_samples: Minimum number of samples to extract
        
    Returns:
        List of conversation dicts in evaluation format
    """
    # Crisis keywords to filter for
    crisis_keywords = [
        'suicide', 'suicidal', 'kill myself', 'end my life',
        'want to die', 'better off dead', 'self harm', 'cut myself',
        'hurt myself', 'overdose', 'jump off', 'hang myself',
        'not worth living', 'no reason to live', 'give up on life'
    ]
    
    safety_critical = []
    
    for sample in samples:
        message_lower = sample.message.lower()
        
        # Check if message contains crisis keywords
        has_crisis_keyword = any(
            keyword in message_lower
            for keyword in crisis_keywords
        )
        
        if has_crisis_keyword or sample.label == "crisis":
            # Convert to evaluation format
            conversation = {
                'id': sample.id,
                'messages': [
                    {'role': 'student', 'content': sample.message}
                ],
                'labels': {
                    'is_crisis': True,
                    'risk_level': 'CRISIS',
                    'source': sample.source
                },
                'metadata': sample.metadata
            }
            safety_critical.append(conversation)
    
    logger.info(
        "extracted_safety_critical",
        total_samples=len(samples),
        safety_critical=len(safety_critical),
        target=min_samples
    )
    
    return safety_critical


def create_balanced_test_set(
    crisis_samples: List[Dict],
    safe_samples: List[ConversationSample],
    crisis_count: int = 500,
    safe_count: int = 500
) -> List[Dict]:
    """
    Create balanced test set with crisis and safe samples.
    
    Args:
        crisis_samples: Crisis conversation dicts
        safe_samples: Safe conversation samples
        crisis_count: Number of crisis samples
        safe_count: Number of safe samples
        
    Returns:
        Balanced test set
    """
    # Take first N crisis samples
    balanced = crisis_samples[:crisis_count]
    
    # Add safe samples
    for sample in safe_samples[:safe_count]:
        conversation = {
            'id': sample.id,
            'messages': [
                {'role': 'student', 'content': sample.message}
            ],
            'labels': {
                'is_crisis': False,
                'risk_level': 'SAFE',
                'source': sample.source
            },
            'metadata': sample.metadata
        }
        balanced.append(conversation)
    
    logger.info(
        "created_balanced_set",
        crisis=crisis_count,
        safe=safe_count,
        total=len(balanced)
    )
    
    return balanced


def main():
    """Download and prepare datasets."""
    # Setup logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    print("\n" + "="*70)
    print("Beacon Dataset Downloader - Milestone 1")
    print("="*70)
    
    # Initialize loader
    loader = DatasetLoader()
    
    # Create output directory
    output_dir = Path("evaluation/datasets/mentalchat16k")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_samples = []
    
    # 1. Download MentalChat16K
    print("\n📥 Downloading MentalChat16K...")
    try:
        train_samples = loader.load_mentalchat16k("train")
        all_samples.extend(train_samples)
        print(f"✅ Downloaded {len(train_samples)} training samples")
    except Exception as e:
        print(f"⚠️  Could not download MentalChat16K: {e}")
    
    # 2. Download EmpatheticDialogues
    print("\n📥 Downloading EmpatheticDialogues...")
    try:
        empathetic_samples = loader.load_empathetic_dialogues("train")
        all_samples.extend(empathetic_samples)
        print(f"✅ Downloaded {len(empathetic_samples)} empathetic samples")
    except Exception as e:
        print(f"⚠️  Could not download EmpatheticDialogues: {e}")
    
    # 3. Try Amod/mental_health_counseling_conversations
    print("\n📥 Downloading Amod/mental_health_counseling...")
    try:
        from datasets import load_dataset
        dataset = load_dataset("Amod/mental_health_counseling_conversations", split="train", cache_dir=str(loader.cache_dir))
        amod_samples = []
        for idx, item in enumerate(dataset):
            message = item.get('Context', item.get('question', ''))
            if message and isinstance(message, str):
                sample = ConversationSample(
                    id=f"amod_{idx}",
                    message=message,
                    context=[],
                    label="unknown",
                    source="Amod",
                    metadata={'response': item.get('Response', '')}
                )
                amod_samples.append(sample)
        all_samples.extend(amod_samples)
        print(f"✅ Downloaded {len(amod_samples)} counseling samples")
    except Exception as e:
        print(f"⚠️  Could not download Amod dataset: {e}")
    
    # 4. Add our hard crisis dataset
    print("\n📥 Loading hard crisis dataset...")
    try:
        hard_crisis = loader.load_hard_crisis_dataset()
        all_samples.extend(hard_crisis)
        print(f"✅ Loaded {len(hard_crisis)} hard crisis samples")
    except Exception as e:
        print(f"⚠️  Could not load hard crisis dataset: {e}")
    
    # 5. Extract safety-critical subset
    print("\n🔍 Extracting safety-critical subset...")
    crisis_samples = extract_safety_critical_subset(all_samples, min_samples=500)
    
    if len(crisis_samples) < 100:
        print(f"⚠️  Only found {len(crisis_samples)} crisis samples")
        print("   This may not be enough for robust evaluation")
    
    # 6. Create balanced test set
    print("\n⚖️  Creating balanced test set...")
    safe_samples = [s for s in all_samples if s.label != "crisis"]
    balanced_set = create_balanced_test_set(
        crisis_samples,
        safe_samples,
        crisis_count=min(len(crisis_samples), 500),
        safe_count=500
    )
    
    # 7. Save datasets
    print("\n💾 Saving datasets...")
    
    # Save safety-critical subset
    safety_critical_path = output_dir / "safety_critical_subset.json"
    with open(safety_critical_path, 'w') as f:
        json.dump({
            'conversations': crisis_samples,
            'metadata': {
                'total_samples': len(crisis_samples),
                'source': 'MentalChat16K + EmpatheticDialogues',
                'description': 'Safety-critical subset with explicit crisis markers'
            }
        }, f, indent=2)
    print(f"✅ Saved safety-critical subset: {safety_critical_path}")
    print(f"   {len(crisis_samples)} crisis samples")
    
    # Save balanced test set
    balanced_path = output_dir / "balanced_test_set.json"
    with open(balanced_path, 'w') as f:
        json.dump({
            'conversations': balanced_set,
            'metadata': {
                'total_samples': len(balanced_set),
                'crisis_samples': len([c for c in balanced_set if c['labels']['is_crisis']]),
                'safe_samples': len([c for c in balanced_set if not c['labels']['is_crisis']]),
                'description': 'Balanced test set for precision/recall evaluation'
            }
        }, f, indent=2)
    print(f"✅ Saved balanced test set: {balanced_path}")
    print(f"   {len(balanced_set)} total samples")
    
    # 8. Generate summary
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)
    print(f"Total samples downloaded:     {len(all_samples)}")
    print(f"Safety-critical subset:       {len(crisis_samples)}")
    print(f"Balanced test set:            {len(balanced_set)}")
    print(f"Output directory:             {output_dir}")
    print("="*70 + "\n")
    
    print("✅ Dataset preparation complete!")
    print("\nNext steps:")
    print("  1. Run evaluation: python evaluation/suites/mentalchat_eval.py")
    print("  2. Review results in evaluation report")
    print("  3. Update MILESTONES.md with completion status\n")


if __name__ == "__main__":
    main()
