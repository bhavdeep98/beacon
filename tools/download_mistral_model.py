"""
Download Mental Health Mistral Model (Q8_0 GGUF)

Downloads the Q8_0 quantized GGUF model for native llama-cpp-python integration.
Model: mradermacher/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF
Size: ~8GB (Q8_0 quantization)

This provides the best quality-to-performance ratio for mental health conversations.
"""

import sys
import os
from pathlib import Path
import urllib.request

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("DOWNLOADING MENTAL HEALTH MISTRAL MODEL (Q8_0 GGUF)")
print("=" * 80)
print()
print("Model: mradermacher/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF")
print("Quantization: Q8_0 (8-bit, high fidelity)")
print("Size: ~8GB")
print("This may take several minutes depending on your connection...")
print()

# Model details
MODEL_URL = "https://huggingface.co/mradermacher/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF/resolve/main/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf"
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf"

# Create models directory
MODEL_DIR.mkdir(exist_ok=True)

# Check if already downloaded
if MODEL_PATH.exists():
    print(f"✅ Model already exists at: {MODEL_PATH}")
    print(f"   Size: {MODEL_PATH.stat().st_size / 1024**3:.2f} GB")
    print()
    print("To re-download, delete the file and run this script again.")
    sys.exit(0)

print(f"Downloading to: {MODEL_PATH}")
print()

def download_progress(block_num, block_size, total_size):
    """Show download progress."""
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 / total_size)
    downloaded_mb = downloaded / 1024**2
    total_mb = total_size / 1024**2
    
    # Update progress bar
    bar_length = 50
    filled = int(bar_length * percent / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    print(f'\r[{bar}] {percent:.1f}% ({downloaded_mb:.0f}/{total_mb:.0f} MB)', end='', flush=True)

try:
    print("Downloading model file...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH, reporthook=download_progress)
    print()  # New line after progress bar
    print()
    
    print("✅ Model downloaded successfully!")
    print()
    print(f"Model location: {MODEL_PATH}")
    print(f"Model size: {MODEL_PATH.stat().st_size / 1024**3:.2f} GB")
    print()
    
    print("=" * 80)
    print("MODEL DOWNLOAD COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Check VRAM: python check_vram.py")
    print("  2. Test agent: python run_agent_demo.py")
    print("  3. Start backend: python backend/main.py")
    print()
    
except KeyboardInterrupt:
    print()
    print()
    print("❌ Download cancelled by user")
    # Clean up partial download
    if MODEL_PATH.exists():
        MODEL_PATH.unlink()
        print("   Partial download removed")
    sys.exit(1)
    
except Exception as e:
    print()
    print()
    print(f"❌ Error downloading model: {e}")
    print()
    print("Possible issues:")
    print("  - Network connection problems")
    print("  - Insufficient disk space (~8GB required)")
    print("  - HuggingFace Hub access issues")
    print()
    print("Alternative: Download manually from:")
    print(f"  {MODEL_URL}")
    print(f"  Save to: {MODEL_PATH}")
    
    # Clean up partial download
    if MODEL_PATH.exists():
        MODEL_PATH.unlink()
    
    sys.exit(1)
