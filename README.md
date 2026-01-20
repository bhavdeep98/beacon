# PsyFlo (Feelwell) - Mental Health AI Triage System

AI-driven crisis detection and mental health triage for school districts and youth organizations.

## Quick Start

```bash
# Setup environment
./setup.sh

# Run tests
./run_tests.sh

# Run interactive demo
python tools/cli_demo.py

# Run benchmarks
python evaluation/benchmark_runner.py --dataset hard_crisis
```

## Project Structure

```
Psyflo-feelwell/
├── src/safety/                    # Safety Service (crisis detection)
│   ├── safety_analyzer.py         # Main orchestrator
│   ├── strategy_factory.py        # Strategy factory
│   └── strategies/                # Detection strategies
│       ├── base.py                # Abstract base
│       ├── regex_strategy.py      # Deterministic keywords
│       ├── semantic_strategy.py   # Embedding similarity
│       └── sarcasm_strategy.py    # Hyperbole filter
├── tests/                         # Unit tests
│   └── test_safety_service.py     # Comprehensive test suite
├── evaluation/                    # Benchmarking & evaluation
│   ├── dataset_loader.py          # Dataset loading
│   ├── benchmark_runner.py        # Benchmark suite
│   └── datasets/                  # Evaluation datasets
├── config/                        # Configuration
│   └── crisis_patterns.yaml       # Crisis detection patterns
├── docs/                          # Documentation
│   ├── HLD.md                     # High-level design
│   ├── LLD.md                     # Low-level design
│   ├── MILESTONES.md              # Project milestones
│   └── DECISION_LOG.md            # Design decisions
└── .kiro/steering/                # Project tenets & standards
```

## Current Status

**Milestone 1**: 70% Complete
- ✅ Safety Service with multi-layer detection
- ✅ Strategy Pattern implementation
- ✅ Comprehensive test suite
- ✅ Benchmark framework
- ⏳ Real-world dataset evaluation

## Key Features

### Multi-Layer Crisis Detection
- **Regex Layer**: Deterministic keyword matching (safety floor)
- **Semantic Layer**: Embedding similarity for obfuscated language
- **Sarcasm Filter**: Reduces false positives from hyperbole

### Performance
- **Latency**: <50ms P95 (target)
- **Throughput**: >20 messages/second
- **Recall**: 100% on explicit keywords (target)

### Design Principles
- Safety First (deterministic guardrails)
- Explicit Over Clever (traceable code)
- Immutability by Default (audit trail)
- Observable Systems (comprehensive logging)

## Testing

```bash
# Run all tests
./run_tests.sh

# Run with coverage
./run_tests.sh --coverage

# Run fast tests only (skip benchmarks)
./run_tests.sh --fast

# Run specific test class
pytest tests/test_safety_service.py::TestExplicitCrisisDetection -v
```

## Benchmarking

```bash
# Benchmark on hard crisis dataset
python evaluation/benchmark_runner.py --dataset hard_crisis

# Benchmark on MentalChat16K
python evaluation/benchmark_runner.py --dataset mentalchat16k

# Benchmark on all datasets
python evaluation/benchmark_runner.py --dataset all
```

## Documentation

- **[High-Level Design](docs/HLD.md)** - System architecture
- **[Low-Level Design](docs/LLD.md)** - Implementation details
- **[Milestones](docs/MILESTONES.md)** - Project roadmap
- **[Project Tenets](.kiro/steering/00-project-tenets.md)** - Design principles

## Development

### Adding Crisis Patterns

Edit `config/crisis_patterns.yaml`:

```yaml
crisis_keywords:
  new_category:
    patterns:
      - "phrase 1"
      - "phrase 2"
    confidence: 0.90
```

Then run tests to validate:

```bash
pytest tests/test_safety_service.py -v
```

### Adding Detection Strategies

1. Create new strategy in `src/safety/strategies/`
2. Inherit from `DetectionStrategy`
3. Implement `analyze()` and `get_name()`
4. Add to factory in `strategy_factory.py`
5. Add tests in `tests/test_safety_service.py`

## License

Proprietary - All Rights Reserved

## Contact

For questions or support, see project documentation.
