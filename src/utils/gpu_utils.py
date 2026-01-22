"""
GPU Memory Management Utilities

Tenet #11: Graceful Degradation - Automatically adapt to available VRAM
Tenet #10: Observable Systems - Log memory allocation decisions
"""

import math
import structlog

logger = structlog.get_logger()


def calculate_optimal_layers(
    model_size_gb: float = 7.7,
    total_layers: int = 33,
    safety_buffer_gb: float = 1.5
) -> int:
    """
    Calculate optimal number of layers to offload to GPU based on available VRAM.
    
    For Mistral 7B Q8_0:
    - Model size: ~7.7GB
    - Total layers: 33
    - Safety buffer: 1.5GB for KV cache, OS, and UI overhead
    
    Args:
        model_size_gb: Size of the GGUF model file in GB
        total_layers: Total number of transformer layers in the model
        safety_buffer_gb: Reserved VRAM for KV cache and system overhead
        
    Returns:
        Number of layers to offload to GPU (0 = CPU only)
        
    Design:
    - Tenet #11: Graceful degradation - Falls back to CPU if insufficient VRAM
    - Tenet #10: Observable - Logs memory allocation decisions
    """
    try:
        import pynvml
        
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # Assumes GPU 0
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        
        # Convert bytes to GB
        total_vram = info.total / 1024**3
        free_vram = info.free / 1024**3
        
        logger.info(
            "gpu_memory_detected",
            total_vram_gb=round(total_vram, 2),
            free_vram_gb=round(free_vram, 2)
        )
        
        # Effective VRAM available for model layers
        available_for_layers = free_vram - safety_buffer_gb
        
        if available_for_layers <= 0:
            logger.warning(
                "insufficient_vram_using_cpu",
                free_vram_gb=round(free_vram, 2),
                safety_buffer_gb=safety_buffer_gb
            )
            return 0
        
        # Calculate memory per layer
        gb_per_layer = model_size_gb / total_layers
        
        # Determine how many layers fit
        offload_layers = math.floor(available_for_layers / gb_per_layer)
        
        # Cap at total_layers
        final_layers = min(offload_layers, total_layers)
        
        logger.info(
            "gpu_layer_optimization",
            offload_layers=final_layers,
            total_layers=total_layers,
            gb_per_layer=round(gb_per_layer, 2),
            available_vram_gb=round(available_for_layers, 2)
        )
        
        return final_layers
        
    except ImportError:
        logger.warning(
            "pynvml_not_available_using_cpu",
            reason="nvidia-ml-py not installed"
        )
        return 0
        
    except Exception as e:
        logger.warning(
            "gpu_detection_failed_using_cpu",
            error=str(e),
            exc_info=True
        )
        return 0
        
    finally:
        try:
            pynvml.nvmlShutdown()
        except:
            pass


def get_gpu_info() -> dict:
    """
    Get detailed GPU information for diagnostics.
    
    Returns:
        Dictionary with GPU details or empty dict if unavailable
    """
    try:
        import pynvml
        
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        name = pynvml.nvmlDeviceGetName(handle)
        
        result = {
            "name": name,
            "total_vram_gb": round(info.total / 1024**3, 2),
            "free_vram_gb": round(info.free / 1024**3, 2),
            "used_vram_gb": round(info.used / 1024**3, 2)
        }
        
        pynvml.nvmlShutdown()
        return result
        
    except Exception as e:
        logger.debug("gpu_info_unavailable", error=str(e))
        return {}
