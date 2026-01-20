#!/bin/bash
# PsyFlo Milestone 1 Setup Script

set -e

echo "=========================================="
echo "PsyFlo Milestone 1 Setup"
echo "=========================================="

# Check Python version
echo ""
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Download sentence-transformers model
echo ""
echo "🤖 Downloading semantic model (all-MiniLM-L6-v2)..."
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
echo "✅ Model downloaded"

# Create necessary directories
echo ""
echo "📁 Creating directories..."
mkdir -p evaluation/datasets/mentalchat16k
mkdir -p evaluation/results
mkdir -p logs
echo "✅ Directories created"

# Run tests
echo ""
echo "🧪 Running tests..."
pytest tests/test_safety_service.py -v

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run CLI demo: python tools/cli_demo.py"
echo "3. Run batch demo: python tools/cli_demo.py --batch"
echo "4. Download MentalChat16K dataset to evaluation/datasets/mentalchat16k/"
echo "5. Run evaluation: python evaluation/suites/mentalchat_eval.py"
echo ""
