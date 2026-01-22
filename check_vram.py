"""
VRAM Check Script

Quick diagnostic to verify GPU detection and layer calculation.
Run this before starting the backend to ensure optimal configuration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.gpu_utils import calculate_optimal_layers, get_gpu_info


def main():
    print("=" * 60)
    print("PsyFlo VRAM Check")
    print("=" * 60)
    print()
    
    # Get GPU info
    gpu_info = get_gpu_info()
    
    if gpu_info:
        print("✓ GPU Detected:")
        print(f"  Name: {gpu_info['name']}")
        print(f"  Total VRAM: {gpu_info['total_vram_gb']} GB")
        print(f"  Free VRAM: {gpu_info['free_vram_gb']} GB")
        print(f"  Used VRAM: {gpu_info['used_vram_gb']} GB")
        print()
    else:
        print("✗ No GPU detected or nvidia-ml-py not installed")
        print("  Will use CPU mode (slower)")
        print()
    
    # Calculate optimal layers
    print("Calculating optimal layer offloading...")
    print()
    
    n_gpu_layers = calculate_optimal_layers(
        model_size_gb=7.7,  # Q8_0 Mistral 7B
        total_layers=33,    # Mistral architecture
        safety_buffer_gb=1.5  # KV cache + overhead
    )
    
    print(f"Recommended Configuration:")
    print(f"  n_gpu_layers: {n_gpu_layers} / 33")
    print()
    
    if n_gpu_layers == 0:
        print("⚠ CPU Mode:")
        print("  - Generation will be slower (10-30s per response)")
        print("  - Consider freeing up VRAM by closing other applications")
        print("  - Or use a machine with more VRAM")
    elif n_gpu_layers < 33:
        print("⚠ Hybrid Mode:")
        print(f"  - {n_gpu_layers} layers on GPU (fast)")
        print(f"  - {33 - n_gpu_layers} layers on CPU (slower)")
        print("  - Expected latency: 3-8s per response")
    else:
        print("✓ Full GPU Mode:")
        print("  - All layers on GPU")
        print("  - Expected latency: 1-3s per response")
    
    print()
    print("=" * 60)
    print("Ready to start backend!")
    print("Run: python backend/main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
