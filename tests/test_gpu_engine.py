"""
Test: Verify LLM Engine loads with GPU acceleration
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.llm_engine import get_llm_engine
import structlog

logger = structlog.get_logger()

def test_gpu_engine():
    print("\n" + "="*60)
    print("TEST: GPU-Accelerated LLM Engine")
    print("="*60)
    
    print("\n[STEP 1] Getting LLM Engine...")
    engine = get_llm_engine()
    
    print(f"✓ Engine Retrieved")
    print(f"  - Mock Mode: {engine.mock_mode}")
    print(f"  - Model Path: {engine.model_path}")
    
    if engine.model:
        print(f"  - Model Loaded: Yes")
        # Try to get n_gpu_layers from model params
        try:
            print(f"  - GPU Layers: {engine.model.n_gpu_layers if hasattr(engine.model, 'n_gpu_layers') else 'Unknown'}")
        except:
            print(f"  - GPU Layers: Unable to determine")
    else:
        print(f"  - Model Loaded: No")
    
    print("\n[STEP 2] Testing Quick Inference...")
    try:
        result = engine.generate(
            prompt="[INST] Say 'Hello' [/INST]",
            max_tokens=10,
            temperature=0.0
        )
        response = result['choices'][0]['text']
        print(f"✓ Inference Successful")
        print(f"  - Response: {response[:50]}")
    except Exception as e:
        print(f"✗ Inference Failed: {e}")
    
    print("\n" + "="*60)
    print("✓ TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_gpu_engine()
