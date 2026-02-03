"""
Shared LLM Engine (Singleton)

Acts as the "Central Hub" for the Expert Mistral Model.
Ensures the 7B model is loaded only once and shared between:
1. The Expert Agent (Clinical Reasoning)
2. The Empathy Agent (Conversation)

Tenet #11: Resource Efficiency - Single model instance in VRAM.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
import threading
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = structlog.get_logger()

# Import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False
    logger.warning("llama_not_installed", detail="Using Mock Mode")

# Import GPU utils
try:
    from src.utils.gpu_utils import calculate_optimal_layers, get_gpu_info
    GPU_UTILS_AVAILABLE = True
    logger.info("gpu_utils_imported_successfully")
except ImportError as e:
    GPU_UTILS_AVAILABLE = False
    logger.warning("gpu_utils_import_failed", error=str(e))

class LLMEngine:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LLMEngine, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.model: Optional[Llama] = None
        self.model_path: Optional[str] = None
        self.mock_mode = not LLAMA_AVAILABLE
        self._load_config()
        self._initialized = True

    def _load_config(self):
        """Determine model path and settings from environment."""
        # Try to find the model in standard locations
        root = Path(__file__).resolve().parent.parent.parent
        default_path = root / "models" / "Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf"
        
        env_path = os.getenv("LLAMA_MODEL_PATH")
        if env_path:
             # Try absolute, then relative to root
             p = Path(env_path)
             if p.exists():
                 self.model_path = str(p)
             elif (root / env_path).exists():
                 self.model_path = str(root / env_path)
             else:
                 self.model_path = str(default_path)
        else:
            self.model_path = str(default_path)
            
        self.context_window = int(os.getenv("LLAMA_CONTEXT_WINDOW", "4096"))

    def load_model(self, force_reload: bool = False):
        """Load the model if not already loaded."""
        if self.mock_mode:
            logger.info("llm_engine_mock_mode_active")
            return

        with self._lock:
            if self.model is not None and not force_reload:
                return

            if not Path(self.model_path).exists():
                logger.error("model_file_not_found", path=self.model_path)
                self.mock_mode = True
                return

            try:
                # Calculate Layers
                n_gpu_layers = 0
                if GPU_UTILS_AVAILABLE:
                    # Provide default values if utils imported but fails specifically
                    try:
                       n_gpu_layers = calculate_optimal_layers(
                            model_size_gb=7.7,
                            total_layers=33,
                            safety_buffer_gb=1.5
                        )
                       logger.info("gpu_layers_calculated", n_gpu_layers=n_gpu_layers)
                    except Exception as e:
                        logger.warning("gpu_layer_calculation_failed", error=str(e))
                        n_gpu_layers = 12  # Fallback conservative (works for 8GB GPU)
                else:
                    logger.warning("gpu_utils_not_available", detail="Using CPU only")
                
                logger.info(
                    "loading_shared_model", 
                    path=self.model_path, 
                    n_gpu_layers=n_gpu_layers
                )

                self.model = Llama(
                    model_path=self.model_path,
                    n_gpu_layers=n_gpu_layers,
                    n_ctx=self.context_window,
                    verbose=False
                )
                
                logger.info("shared_model_loaded_successfully")
                
            except Exception as e:
                logger.error("shared_model_load_failed", error=str(e))
                self.mock_mode = True
                raise

    def generate(self, prompt: str, **kwargs) -> Any:
        """
        Thread-safe generation wrapper.
        Wrapper for create_completion
        """
        if self.mock_mode or not self.model:
            return self._mock_response(**kwargs)
            
        with self._lock:
            return self.model.create_completion(prompt, **kwargs)

    def chat(self, messages: List[Dict], **kwargs) -> Any:
        """
        Thread-safe chat wrapper.
        Wrapper for create_chat_completion
        """
        if self.mock_mode or not self.model:
            return self._mock_chat_response(**kwargs)

        with self._lock:
            return self.model.create_chat_completion(messages=messages, **kwargs)

    def _mock_response(self, stream=False, **kwargs):
        text = "MOCK_RESPONSE: The shared engine is in mock mode."
        if stream:
            def gen():
                yield {"choices": [{"text": text, "finish_reason": "stop"}]}
            return gen()
        return {"choices": [{"text": text, "finish_reason": "stop"}]}

    def _mock_chat_response(self, stream=False, **kwargs):
        content = "MOCK_CHAT: The shared engine is in mock mode."
        if stream:
            def gen():
                yield {"choices": [{"delta": {"content": content}, "finish_reason": None}]}
                yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}
            return gen()
        return {"choices": [{"message": {"content": content}, "finish_reason": "stop"}]}

# Global accessor
def get_llm_engine() -> LLMEngine:
    engine = LLMEngine()
    # Lazy load on first access
    if not engine.model and not engine.mock_mode:
        try:
            engine.load_model()
        except Exception as e:
            logger.warning("auto_load_llm_failed", error=str(e))
    return engine
