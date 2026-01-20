"""
Benchmark Runner for Safety Service

Runs comprehensive benchmarks against multiple datasets:
- MentalChat16K
- EmpatheticDialogues  
- Hard Crisis Dataset
- Custom datasets

Metrics:
- Recall (sensitivity)
- Precision
- F1 Score
- Latency (P50, P95, P99)
- False Positive Rate
- False Negative Rate

Usage:
    python evaluation/benchmark_runner.py --dataset mentalchat16k
    python evaluation/benchmark_runner.py --dataset all
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import time
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.safety.safety_analyzer import SafetyService
from evaluation.dataset_loader import DatasetLoader, ConversationSample
import structlog

logger = structlog.get_logger()


@dataclass
class BenchmarkMetrics:
    """Benchmark evaluation metrics."""
    dataset_name: str
    total_samples: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    latencies_ms: List[float]
    
    @property
    def recall(self) -> float:
        """Sensitivity: TP / (TP + FN)"""
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        """F1: 2 * (precision * recall) / (precision + recall)"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def accuracy(self) -> float:
        """Accuracy: (TP + TN) / Total"""
        total = self.true_positives + self.false_positives + self.true_negatives + self.false_negatives
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0
    
    @property
    def false_positive_rate(self) -> float:
        """FPR: FP / (FP + TN)"""
        denom = self.false_positives + self.true_negatives
        return self.false_positives / denom if denom > 0 else 0.0
    
    def latency_percentile(self, percentile: int) -> float:
        """Calculate latency percentile."""
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        idx = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]


class BenchmarkRunner:
    """
    Runs comprehensive benchmarks on Safety Service.
    
    Evaluates against multiple datasets and generates detailed reports.
    """
    
    def __init__(self, safety_service: SafetyService, dataset_loader: DatasetLoader):
        """
        Initialize benchmark runner.
        
        Args:
            safety_service: SafetyService instance to benchmark
            dataset_loader: DatasetLoader for loading datasets
        """
        self.safety_service = safety_service
        self.dataset_loader = dataset_loader
    
    def run_benchmark(
        self,
        samples: List[ConversationSample],
        dataset_name: str
    ) -> BenchmarkMetrics:
        """
        Run benchmark on dataset samples.
        
        Args:
            samples: List of conversation samples
            dataset_name: Name of dataset for reporting
            
        Returns:
            BenchmarkMetrics with results
        """
        print(f"\n{'='*70}")
        print(f"Benchmarking: {dataset_name}")
        print(f"{'='*70}")
        print(f"Total samples: {len(samples)}")
        
        metrics = BenchmarkMetrics(
            dataset_name=dataset_name,
            total_samples=len(samples),
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0,
            latencies_ms=[]
        )
        
        for idx, sample in enumerate(samples):
            # Run safety analysis
            result = self.safety_service.analyze(sample.message, sample.context)
            
            # Record latency
            metrics.latencies_ms.append(result.latency_ms)
            
            # Determine ground truth
            actual_crisis = sample.label in ["crisis", "caution"]
            predicted_crisis = result.is_crisis
            
            # Update confusion matrix
            if predicted_crisis and actual_crisis:
                metrics.true_positives += 1
            elif predicted_crisis and not actual_crisis:
                metrics.false_positives += 1
                logger.warning(
                    "false_positive",
                    message=sample.message[:100],
                    p_regex=result.p_regex,
                    p_semantic=result.p_semantic
                )
            elif not predicted_crisis and actual_crisis:
                metrics.false_negatives += 1
                logger.error(
                    "false_negative",
                    message=sample.message[:100],
                    label=sample.label,
                    p_regex=result.p_regex,
                    p_semantic=result.p_semantic
                )
            else:
                metrics.true_negatives += 1
            
            # Progress indicator
            if (idx + 1) % 100 == 0:
                print(f"  Processed {idx + 1}/{len(samples)} samples...")
        
        return metrics
    
    def print_report(self, metrics: BenchmarkMetrics):
        """Print detailed benchmark report."""
        print(f"\n{'='*70}")
        print(f"BENCHMARK REPORT: {metrics.dataset_name}")
        print(f"{'='*70}")
        
        print(f"\n📊 Classification Metrics:")
        print(f"  Recall (Sensitivity):  {metrics.recall:.3f} ({metrics.recall*100:.1f}%)")
        print(f"  Precision:             {metrics.precision:.3f} ({metrics.precision*100:.1f}%)")
        print(f"  F1 Score:              {metrics.f1_score:.3f}")
        print(f"  Accuracy:              {metrics.accuracy:.3f} ({metrics.accuracy*100:.1f}%)")
        print(f"  False Positive Rate:   {metrics.false_positive_rate:.3f} ({metrics.false_positive_rate*100:.1f}%)")
        
        print(f"\n🎯 Confusion Matrix:")
        print(f"  True Positives:   {metrics.true_positives}")
        print(f"  False Positives:  {metrics.false_positives}")
        print(f"  True Negatives:   {metrics.true_negatives}")
        print(f"  False Negatives:  {metrics.false_negatives}")
        
        print(f"\n⚡ Latency Metrics:")
        print(f"  P50 (Median):  {metrics.latency_percentile(50):.2f}ms")
        print(f"  P95:           {metrics.latency_percentile(95):.2f}ms")
        print(f"  P99:           {metrics.latency_percentile(99):.2f}ms")
        print(f"  Max:           {max(metrics.latencies_ms):.2f}ms")
        
        print(f"\n✅ SLA Compliance:")
        print(f"  Recall ≥99%:       {'✅ PASS' if metrics.recall >= 0.99 else '❌ FAIL'}")
        print(f"  Latency P95 <50ms: {'✅ PASS' if metrics.latency_percentile(95) < 50 else '❌ FAIL'}")
        print(f"  FPR <10%:          {'✅ PASS' if metrics.false_positive_rate < 0.10 else '❌ FAIL'}")
        
        print(f"{'='*70}\n")
    
    def save_report(self, metrics: BenchmarkMetrics, output_path: str):
        """Save benchmark report to JSON file."""
        report = {
            'dataset_name': metrics.dataset_name,
            'total_samples': metrics.total_samples,
            'metrics': {
                'recall': metrics.recall,
                'precision': metrics.precision,
                'f1_score': metrics.f1_score,
                'accuracy': metrics.accuracy,
                'false_positive_rate': metrics.false_positive_rate
            },
            'confusion_matrix': {
                'true_positives': metrics.true_positives,
                'false_positives': metrics.false_positives,
                'true_negatives': metrics.true_negatives,
                'false_negatives': metrics.false_negatives
            },
            'latency': {
                'p50': metrics.latency_percentile(50),
                'p95': metrics.latency_percentile(95),
                'p99': metrics.latency_percentile(99),
                'max': max(metrics.latencies_ms) if metrics.latencies_ms else 0
            }
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✓ Report saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run Safety Service benchmarks")
    parser.add_argument(
        '--dataset',
        choices=['hard_crisis', 'mentalchat16k', 'empathetic', 'all'],
        default='hard_crisis',
        help='Dataset to benchmark against'
    )
    parser.add_argument(
        '--output',
        default='evaluation/results',
        help='Output directory for reports'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer()
        ]
    )
    
    print("\n" + "="*70)
    print("PsyFlo Safety Service - Benchmark Suite")
    print("="*70)
    
    # Initialize services
    print("\n🔧 Initializing Safety Service...")
    safety_service = SafetyService("config/crisis_patterns.yaml")
    print("✅ Safety Service initialized")
    
    print("\n📂 Initializing Dataset Loader...")
    dataset_loader = DatasetLoader()
    print("✅ Dataset Loader initialized")
    
    # Initialize benchmark runner
    runner = BenchmarkRunner(safety_service, dataset_loader)
    
    # Run benchmarks
    datasets_to_run = []
    
    if args.dataset == 'all':
        datasets_to_run = ['hard_crisis', 'mentalchat16k', 'empathetic']
    else:
        datasets_to_run = [args.dataset]
    
    for dataset_name in datasets_to_run:
        try:
            # Load dataset
            if dataset_name == 'hard_crisis':
                samples = dataset_loader.load_hard_crisis_dataset()
            elif dataset_name == 'mentalchat16k':
                samples = dataset_loader.load_mentalchat16k("test")
            elif dataset_name == 'empathetic':
                samples = dataset_loader.load_empathetic_dialogues("test")
            
            # Run benchmark
            start_time = time.time()
            metrics = runner.run_benchmark(samples, dataset_name)
            elapsed = time.time() - start_time
            
            # Print report
            runner.print_report(metrics)
            
            # Save report
            output_path = f"{args.output}/{dataset_name}_report.json"
            runner.save_report(metrics, output_path)
            
            print(f"⏱️  Total benchmark time: {elapsed:.2f}s")
            print(f"📈 Throughput: {len(samples)/elapsed:.1f} samples/second\n")
            
        except Exception as e:
            print(f"❌ Error benchmarking {dataset_name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
