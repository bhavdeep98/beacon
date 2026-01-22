"""
Tests for GPU Utilities

Tenet #3: Explicit Over Clever - Clear test cases for VRAM calculation
Tenet #10: Observable Systems - Verify logging behavior
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.gpu_utils import calculate_optimal_layers, get_gpu_info


class TestCalculateOptimalLayers:
    """Test VRAM-based layer calculation."""
    
    @patch('utils.gpu_utils.pynvml')
    def test_sufficient_vram_full_offload(self, mock_pynvml):
        """Test full GPU offload when sufficient VRAM available."""
        # Mock 12GB free VRAM (enough for full model + buffer)
        mock_info = Mock()
        mock_info.total = 16 * 1024**3  # 16GB total
        mock_info.free = 12 * 1024**3   # 12GB free
        
        mock_handle = Mock()
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_info
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        
        # Calculate layers
        n_layers = calculate_optimal_layers(
            model_size_gb=7.7,
            total_layers=33,
            safety_buffer_gb=1.5
        )
        
        # Should offload all 33 layers
        assert n_layers == 33
    
    @patch('utils.gpu_utils.pynvml')
    def test_partial_vram_partial_offload(self, mock_pynvml):
        """Test partial GPU offload when limited VRAM available."""
        # Mock 4GB free VRAM (only enough for ~10 layers)
        mock_info = Mock()
        mock_info.total = 8 * 1024**3   # 8GB total
        mock_info.free = 4 * 1024**3    # 4GB free
        
        mock_handle = Mock()
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_info
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        
        # Calculate layers
        n_layers = calculate_optimal_layers(
            model_size_gb=7.7,
            total_layers=33,
            safety_buffer_gb=1.5
        )
        
        # Should offload partial layers
        # (4GB - 1.5GB buffer) / (7.7GB / 33 layers) = ~10 layers
        assert 8 <= n_layers <= 12
    
    @patch('utils.gpu_utils.pynvml')
    def test_insufficient_vram_cpu_fallback(self, mock_pynvml):
        """Test CPU fallback when insufficient VRAM."""
        # Mock 1GB free VRAM (not enough even with buffer)
        mock_info = Mock()
        mock_info.total = 4 * 1024**3   # 4GB total
        mock_info.free = 1 * 1024**3    # 1GB free
        
        mock_handle = Mock()
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_info
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        
        # Calculate layers
        n_layers = calculate_optimal_layers(
            model_size_gb=7.7,
            total_layers=33,
            safety_buffer_gb=1.5
        )
        
        # Should use CPU only
        assert n_layers == 0
    
    def test_pynvml_not_available(self):
        """Test graceful fallback when pynvml not installed."""
        # This will naturally fail to import pynvml in test environment
        with patch('utils.gpu_utils.pynvml', None):
            n_layers = calculate_optimal_layers()
            
            # Should fallback to CPU
            assert n_layers == 0
    
    @patch('utils.gpu_utils.pynvml')
    def test_gpu_detection_error(self, mock_pynvml):
        """Test graceful handling of GPU detection errors."""
        # Mock GPU detection failure
        mock_pynvml.nvmlInit.side_effect = Exception("GPU not found")
        
        n_layers = calculate_optimal_layers()
        
        # Should fallback to CPU
        assert n_layers == 0


class TestGetGPUInfo:
    """Test GPU information retrieval."""
    
    @patch('utils.gpu_utils.pynvml')
    def test_get_gpu_info_success(self, mock_pynvml):
        """Test successful GPU info retrieval."""
        # Mock GPU info
        mock_info = Mock()
        mock_info.total = 8 * 1024**3
        mock_info.free = 6 * 1024**3
        mock_info.used = 2 * 1024**3
        
        mock_handle = Mock()
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = mock_info
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = mock_handle
        mock_pynvml.nvmlDeviceGetName.return_value = "NVIDIA GeForce RTX 3070"
        
        info = get_gpu_info()
        
        assert info["name"] == "NVIDIA GeForce RTX 3070"
        assert info["total_vram_gb"] == 8.0
        assert info["free_vram_gb"] == 6.0
        assert info["used_vram_gb"] == 2.0
    
    @patch('utils.gpu_utils.pynvml')
    def test_get_gpu_info_failure(self, mock_pynvml):
        """Test graceful handling of GPU info retrieval failure."""
        mock_pynvml.nvmlInit.side_effect = Exception("GPU error")
        
        info = get_gpu_info()
        
        # Should return empty dict
        assert info == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
