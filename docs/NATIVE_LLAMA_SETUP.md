# Native Llama Integration Setup

This guide covers the migration from ChatOpenAI (LangChain) to native llama-cpp-python integration for the Q8_0 quantized Mistral model.

## Overview

**Why Native Llama?**
- **Higher Fidelity**: Q8_0 quantization preserves emotional nuance critical for mental health conversations
- **Direct Control**: Manage VRAM allocation and layer offloading explicitly
- **No Server Overhead**: No separate Ollama service consuming resources
- **Empathic Latency**: 5-10s generation time feels natural with proper UX (streaming tokens)

**Model Details:**
- Model: `mradermacher/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF`
- Quantization: Q8_0 (8-bit, high fidelity)
- Size: ~8GB
- Architecture: Mistral 7B (33 layers)

## Prerequisites

### 1. Hardware Requirements

**Minimum:**
- CPU: Modern multi-core processor
- RAM: 16GB system RAM
- Disk: 10GB free space

**Recommended:**
- GPU: NVIDIA GPU with 8GB+ VRAM (RTX 3070, RTX 4060, or better)
- RAM: 32GB system RAM
- Disk: 20GB free space (for model + cache)

**VRAM Allocation:**
- Full GPU (8GB+ VRAM): All 33 layers on GPU → 1-3s latency
- Hybrid (4-8GB VRAM): Partial layers on GPU → 3-8s latency
- CPU Only (<4GB VRAM): All layers on CPU → 10-30s latency

### 2. Software Requirements

**Windows:**
- Python 3.11+
- Visual Studio Build Tools (for llama-cpp-python compilation)
- CUDA Toolkit 12.x (for GPU support)
- CMake 3.21+

**Installation:**
```powershell
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/
# Select "Desktop development with C++"

# Install CUDA Toolkit
# Download from: https://developer.nvidia.com/cuda-downloads

# Install CMake
choco install cmake
# Or download from: https://cmake.org/download/
```

## Installation Steps

### Step 1: Install Dependencies

```powershell
# Install llama-cpp-python with CUDA support
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python

# Install VRAM detection library
pip install nvidia-ml-py

# Install other dependencies
pip install -r requirements.txt
```

**Troubleshooting:**
- If compilation fails, ensure Visual Studio Build Tools are installed
- If CUDA not detected, verify CUDA Toolkit installation and PATH
- For CPU-only mode, omit the CMAKE_ARGS: `pip install llama-cpp-python`

### Step 2: Download Model

```powershell
# Download Q8_0 GGUF model (~8GB)
python tools/download_mistral_model.py
```

This will download the model to `models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf`

**Manual Download (if script fails):**
1. Visit: https://huggingface.co/mradermacher/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2-GGUF
2. Download: `Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf`
3. Save to: `models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf`

### Step 3: Check VRAM Configuration

```powershell
# Verify GPU detection and optimal layer calculation
python check_vram.py
```

**Expected Output:**
```
✓ GPU Detected:
  Name: NVIDIA GeForce RTX 3070
  Total VRAM: 8.0 GB
  Free VRAM: 7.2 GB
  Used VRAM: 0.8 GB

Recommended Configuration:
  n_gpu_layers: 33 / 33

✓ Full GPU Mode:
  - All layers on GPU
  - Expected latency: 1-3s per response
```

### Step 4: Test Agent

```powershell
# Run demo conversation
python run_agent_demo.py
```

This will test the agent with 3 scenarios:
1. SAFE: Stress about exams
2. CAUTION: Anxiety symptoms
3. CRISIS: Suicidal ideation (triggers hard-coded protocol)

### Step 5: Start Backend

```powershell
# Start FastAPI backend
python backend/main.py
```

The backend will automatically:
1. Detect available VRAM
2. Calculate optimal layer offloading
3. Load the Llama model
4. Start serving on http://localhost:8000

## Configuration

### Environment Variables (.env)

```bash
# Native Llama Configuration
LLAMA_MODEL_PATH=models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf
LLAMA_TEMPERATURE=0.7
USE_NATIVE_LLAMA=true
```

### Manual Layer Configuration

If automatic detection doesn't work, you can manually set layers:

```python
# In src/conversation/conversation_agent.py
agent = ConversationAgent()

# Override automatic detection
agent.llm = Llama(
    model_path="models/Mental-Health-FineTuned-Mistral-7B-Instruct-v0.2.Q8_0.gguf",
    n_gpu_layers=20,  # Manually set to 20 layers
    n_ctx=4096,
    temperature=0.7
)
```

## UX Strategy: "Empathic Latency"

The Q8_0 model takes 5-10s to generate responses. We turn this into a feature:

### Frontend Implementation

```javascript
// Stream tokens to create "thinking" effect
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({ message, session_id })
});

// Show "Connor is reflecting on what you've shared..."
setStatus('thinking');

// Stream response character by character
const text = await response.text();
for (const char of text) {
  appendToResponse(char);
  await sleep(20); // 20ms per character
}
```

### Why This Works

- **Perceived Empathy**: Delay feels like the AI is "working harder" to understand
- **Natural Pacing**: Mimics human typing speed
- **Reduces Anxiety**: Immediate responses can feel robotic
- **Builds Trust**: Students feel heard, not processed

## Performance Optimization

### VRAM Management

The system automatically manages VRAM with a safety buffer:

```python
# Automatic calculation
n_gpu_layers = calculate_optimal_layers(
    model_size_gb=7.7,      # Q8_0 model size
    total_layers=33,        # Mistral architecture
    safety_buffer_gb=1.5    # KV cache + overhead
)
```

**Safety Buffer Explained:**
- KV Cache grows with conversation length
- OS and UI consume VRAM
- Without buffer, system will "spill" to shared memory (10-50x slower)

### Latency Targets

| Mode | Layers | VRAM | Latency | Use Case |
|------|--------|------|---------|----------|
| Full GPU | 33/33 | 8GB+ | 1-3s | Production |
| Hybrid | 15-25/33 | 4-8GB | 3-8s | Development |
| CPU Only | 0/33 | <4GB | 10-30s | Testing |

## Monitoring

### Check GPU Usage

```powershell
# Real-time VRAM monitoring
nvidia-smi -l 1
```

### Backend Logs

The backend logs all VRAM decisions:

```
gpu_memory_detected total_vram_gb=8.0 free_vram_gb=7.2
gpu_layer_optimization offload_layers=33 total_layers=33
llama_model_loaded model_path=models/... n_gpu_layers=33 mode=native
```

## Troubleshooting

### Issue: "Model file not found"

**Solution:**
```powershell
python tools/download_mistral_model.py
```

### Issue: "llama-cpp-python not installed"

**Solution:**
```powershell
$env:CMAKE_ARGS="-DGGML_CUDA=on"
pip install llama-cpp-python
```

### Issue: "CUDA not detected"

**Solution:**
1. Install CUDA Toolkit 12.x
2. Verify: `nvcc --version`
3. Reinstall llama-cpp-python with CMAKE_ARGS

### Issue: "Out of memory" during generation

**Solution:**
1. Close other GPU applications
2. Reduce `n_gpu_layers` manually
3. Use CPU mode: `n_gpu_layers=0`

### Issue: Generation is very slow

**Check:**
1. Run `check_vram.py` to verify GPU detection
2. Check `nvidia-smi` to see if GPU is being used
3. Verify `n_gpu_layers > 0` in logs

## Testing

### Unit Tests

```powershell
# Test GPU utilities
pytest tests/test_gpu_utils.py -v

# Test conversation agent
pytest tests/test_conversation_agent_native.py -v
```

### Integration Tests

```powershell
# Test full conversation flow
pytest tests/test_integration_e2e.py -v
```

## Migration from Ollama

If you were using Ollama previously:

1. **Keep .env settings**: Legacy OpenAI config is preserved for compatibility
2. **Set USE_NATIVE_LLAMA=true**: Enables native mode
3. **Download Q8_0 model**: Higher quality than Ollama's default quantization
4. **No Ollama service needed**: Native integration runs in-process

## Performance Comparison

| Metric | Ollama (Q4) | Native (Q8_0) |
|--------|-------------|---------------|
| Model Size | 4GB | 8GB |
| VRAM Usage | 4-5GB | 8-9GB |
| Latency (GPU) | 2-4s | 1-3s |
| Quality | Good | Excellent |
| Emotional Nuance | Moderate | High |
| False Positives | Higher | Lower |

## Next Steps

1. **Run check_vram.py**: Verify GPU configuration
2. **Run run_agent_demo.py**: Test conversation generation
3. **Start backend**: `python backend/main.py`
4. **Start frontend**: `cd frontend && npm run dev`
5. **Test in browser**: http://localhost:5173

## Support

For issues or questions:
1. Check logs in backend console
2. Run diagnostic scripts (check_vram.py, run_agent_demo.py)
3. Review this documentation
4. Check project tenets in `.kiro/steering/00-project-tenets.md`

---

**Remember**: The stakes are high. Mental health + minors = zero tolerance for bugs.
