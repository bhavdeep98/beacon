#!/usr/bin/env python3
"""
MentalChat16K Evaluation Suite

Evaluates Safety Service against MentalChat16K dataset.

Metrics:
- Recall (sensitivity): % of actual crises detected
- Precision: % of crisis alerts that were actual crises
- F1 Score: Harmonic mean of precision and recall
- Latency: P50, P95, P99
"""

import sys
import json
from pathlib import Path
from typing import List, Dict
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.safety.service import SafetyService
import structlog

logger = structlog.get_logger()


class EvaluationMetrics:
    """Calculate evaluation metrics."""
    
    def __init__(self):
        self.true_positives = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
        self.latencies = []
    
    def add_result(self, predicted: bool, actual: bool, latency_ms: float):
        """Add a single result."""
        if predicted and actual:
            self.true_positives += 1
        elif predicted and not actual:
            self.false_positives += 1
        elif not predicted and actual:
            self.false_negatives += 1
        else:
            self.true_negatives += 1
        
        self.latencies.append(latency_ms)
    
    @property
    def recall(self) -> float:
        """Calculate recall (sensitivity)."""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def precision(self) -> float:
        """Calculate precision."""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def f1_score(self) -> float:
        """Calculate F1 score."""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy."""
        total = (self.true_positives + self.false_positives + 
                self.true_negatives + self.false_negatives)
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    def latency_percentile(self, percentile: int) -> float:
        """Calculate latency percentile."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]
    
    def print_report(self):
        """Print evaluation report."""
        print("\n" + "="*70)
        print("EVALUATION REPORT")
        print("="*70)
        
        print("\n📊 Classification Metrics:")
        print(f"  Recall (Sensitivity):  {self.recall:.3f} ({self.recall*100:.1f}%)")
        print(f"  Precision:             {self.precision:.3f} ({self.precision*100:.1f}%)")
        print(f"  F1 Score:              {self.f1_score:.3f}")
        print(f"  Accuracy:              {self.accuracy:.3f} ({self.accuracy*100:.1f}%)")
        
        print("\n🎯 Confusion Matrix:")
        print(f"  True Positives:   {self.true_positives}")
        print(f"  False Positives:  {self.false_positives}")
        print(f"  True Negatives:   {self.true_negatives}")
        print(f"  False Negatives:  {self.false_negatives}")
        
        print("\n⚡ Latency Metrics:")
        print(f"  P50 (Median):  {self.latency_percentile(50):.2f}ms")
        print(f"  P95:           {self.latency_percentile(95):.2f}ms")
        print(f"  P99:           {self.latency_percentile(99):.2f}ms")
        print(f"  Max:           {max(self.latencies):.2f}ms")
        
        print("\n✅ SLA Compliance:")
        print(f"  Recall ≥99%:       {'✅ PASS' if self.recall >= 0.99 else '❌ FAIL'}")
        print(f"  Latency <50ms:     {'✅ PASS' if self.latency_percentile(95) < 50 else '❌ FAIL'}")
        
        print("="*70 + "\n")


def load_dataset(dataset_path: str) -> List[Dict]:
    """Load evaluation dataset."""
    path = Path(dataset_path)
    
    if not path.exists():
        logger.error("dataset_not_found", path=dataset_path)
        return []
    
    with open(path) as f:
        data = json.load(f)
    
    return data.get('conversations', [])


def evaluate_safety_service(
    service: SafetyService,
    dataset: List[Dict]
) -> EvaluationMetrics:
    """
    Evaluate Safety Service on dataset.
    
    Args:
        service: SafetyService instance
        dataset: List of conversation dicts
        
    Returns:
        EvaluationMetrics with results
    """
    metrics = EvaluationMetrics()
    
    print(f"\n🔍 Evaluating {len(dataset)} conversations...")
    
    for i, conversation in enumerate(dataset):
        # Get last student message
        student_messages = [
            msg for msg in conversation['messages']
            if msg['role'] == 'student'
        ]
        
        if not student_messages:
            continue
        
        message = student_messages[-1]['content']
        actual_crisis = conversation['labels']['is_crisis']
        
        # Analyze with Safety Service
        result = service.analyze(message)
        
        # Record result
        metrics.add_result(
            predicted=result.is_crisis,
            actual=actual_crisis,
            latency_ms=result.latency_ms
        )
        
        # Log false negatives (missed crises)
        if actual_crisis and not result.is_crisis:
            logger.warning(
                "false_negative",
                message=message[:100],
                p_regex=result.p_regex,
                p_semantic=result.p_semantic
            )
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(dataset)} conversations...")
    
    return metrics


def main():
    """Main entry point."""
    # Setup logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    print("\n" + "="*70)
    print("PsyFlo Safety Service - MentalChat16K Evaluation")
    print("="*70)
    
    # Initialize Safety Service
    print("\n🔧 Initializing Safety Service...")
    service = SafetyService(patterns_path="config/crisis_patterns.yaml")
    print("✅ Safety Service initialized")
    
    # Load dataset
    dataset_path = "evaluation/datasets/mentalchat16k/safety_critical_subset.json"
    print(f"\n📂 Loading dataset: {dataset_path}")
    dataset = load_dataset(dataset_path)
    
    if not dataset:
        print("❌ No dataset found. Please download MentalChat16K dataset.")
        print("   See evaluation/datasets/README.md for instructions.")
        return
    
    print(f"✅ Loaded {len(dataset)} conversations")
    
    # Run evaluation
    start_time = time.time()
    metrics = evaluate_safety_service(service, dataset)
    elapsed = time.time() - start_time
    
    # Print report
    metrics.print_report()
    
    print(f"⏱️  Total evaluation time: {elapsed:.2f}s")
    print(f"📈 Throughput: {len(dataset)/elapsed:.1f} conversations/second\n")


if __name__ == "__main__":
    main()
