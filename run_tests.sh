#!/bin/bash
# Test Runner for PsyFlo Safety Service
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh --fast       # Run fast tests only (no benchmarks)
#   ./run_tests.sh --coverage   # Run with coverage report

set -e

echo "=========================================="
echo "PsyFlo Safety Service - Test Suite"
echo "=========================================="

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Parse arguments
FAST_MODE=false
COVERAGE=false

for arg in "$@"; do
    case $arg in
        --fast)
            FAST_MODE=true
            ;;
        --coverage)
            COVERAGE=true
            ;;
    esac
done

# Run unit tests
echo ""
echo "🧪 Running Unit Tests..."
echo "=========================================="

if [ "$COVERAGE" = true ]; then
    pytest tests/test_safety_service.py -v \
        --cov=src/safety \
        --cov-report=term-missing \
        --cov-report=html
    echo ""
    echo "✓ Coverage report generated: htmlcov/index.html"
else
    pytest tests/test_safety_service.py -v
fi

# Run benchmarks (unless fast mode)
if [ "$FAST_MODE" = false ]; then
    echo ""
    echo "📊 Running Benchmarks..."
    echo "=========================================="
    python evaluation/benchmark_runner.py --dataset hard_crisis
fi

echo ""
echo "=========================================="
echo "✅ All Tests Passed!"
echo "=========================================="
