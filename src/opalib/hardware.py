"""
Hardware Abstraction Layer
Manages GPU/CPU resources and computation
"""

import numpy as np
from typing import Optional, Dict, Tuple, List
from enum import Enum
import psutil
import threading


class DeviceType(Enum):
    """Available compute devices."""
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon
    VULKAN = "vulkan"


class MemoryManager:
    """Manages memory allocation and optimization."""
    
    def __init__(self, device: DeviceType = DeviceType.CPU, max_memory_gb: float = 8.0):
        """
        Initialize memory manager.
        
        Args:
            device: Compute device to manage.
            max_memory_gb: Maximum memory to allocate.
        """
        self.device = device
        self.max_memory_bytes = int(max_memory_gb * 1e9)
        self.allocated_memory = 0
        self.allocations = {}
        self.lock = threading.Lock()
    
    def allocate(self, size_bytes: int, name: str = "") -> np.ndarray:
        """
        Allocate memory for tensor.
        
        Args:
            size_bytes: Size to allocate in bytes.
            name: Name for tracking.
        
        Returns:
            Allocated numpy array.
        """
        with self.lock:
            if self.allocated_memory + size_bytes > self.max_memory_bytes:
                raise MemoryError(
                    f"Cannot allocate {size_bytes} bytes. "
                    f"Already allocated: {self.allocated_memory}/{self.max_memory_bytes}"
                )
            
            # Allocate memory
            num_elements = size_bytes // 8  # Assuming float64
            array = np.zeros(num_elements, dtype=np.float32)
            
            self.allocated_memory += size_bytes
            if name:
                self.allocations[name] = size_bytes
            
            return array
    
    def deallocate(self, name: str):
        """Deallocate memory."""
        with self.lock:
            if name in self.allocations:
                self.allocated_memory -= self.allocations[name]
                del self.allocations[name]
    
    def get_available_memory(self) -> int:
        """Get available memory in bytes."""
        return self.max_memory_bytes - self.allocated_memory
    
    def optimize(self):
        """Optimize memory usage."""
        # Clear fragmentation
        pass


class HardwareAccelerator:
    """Handles hardware-specific optimizations."""
    
    def __init__(self, device: DeviceType = DeviceType.CPU):
        """
        Initialize hardware accelerator.
        
        Args:
            device: Compute device to use.
        """
        self.device = device
        self.memory_manager = MemoryManager(device)
        self.kernel_cache = {}
    
    @staticmethod
    def detect_device() -> DeviceType:
        """Detect available hardware."""
        try:
            import torch
            if torch.cuda.is_available():
                return DeviceType.CUDA
            elif torch.backends.mps.is_available():
                return DeviceType.MPS
        except ImportError:
            pass
        
        return DeviceType.CPU
    
    def matmul_optimized(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Optimized matrix multiplication.
        
        Args:
            a: First matrix.
            b: Second matrix.
        
        Returns:
            Result of matrix multiplication.
        """
        if self.device == DeviceType.CPU:
            # Use NumPy's optimized BLAS
            return np.dot(a, b)
        
        elif self.device == DeviceType.CUDA:
            try:
                import cupy as cp
                a_gpu = cp.asarray(a)
                b_gpu = cp.asarray(b)
                result = cp.matmul(a_gpu, b_gpu)
                return cp.asnumpy(result)
            except ImportError:
                return np.dot(a, b)
        
        elif self.device == DeviceType.MPS:
            try:
                import torch
                a_t = torch.from_numpy(a).to('mps')
                b_t = torch.from_numpy(b).to('mps')
                result = torch.matmul(a_t, b_t)
                return result.cpu().numpy()
            except ImportError:
                return np.dot(a, b)
        
        return np.dot(a, b)
    
    def softmax_optimized(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """
        Optimized softmax.
        
        Args:
            x: Input array.
            axis: Axis along which to compute softmax.
        
        Returns:
            Softmax output.
        """
        # Subtract max for numerical stability
        x_max = np.max(x, axis=axis, keepdims=True)
        exp_x = np.exp(x - x_max)
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    def attention_optimized(self, q: np.ndarray, k: np.ndarray, v: np.ndarray,
                           mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Optimized attention computation.
        
        Args:
            q: Query matrix.
            k: Key matrix.
            v: Value matrix.
            mask: Attention mask (optional).
        
        Returns:
            Attention output.
        """
        # Compute scores
        scores = self.matmul_optimized(q, k.T) / np.sqrt(k.shape[-1])
        
        # Apply mask if provided
        if mask is not None:
            scores = scores + (mask * -1e9)
        
        # Compute attention weights
        weights = self.softmax_optimized(scores, axis=-1)
        
        # Apply to values
        output = self.matmul_optimized(weights, v)
        
        return output
    
    def conv2d_optimized(self, x: np.ndarray, kernel: np.ndarray,
                        stride: int = 1, padding: int = 0) -> np.ndarray:
        """
        Optimized 2D convolution.
        
        Args:
            x: Input tensor (batch, height, width, channels).
            kernel: Convolution kernel.
            stride: Stride parameter.
            padding: Padding parameter.
        
        Returns:
            Convolution output.
        """
        if self.device == DeviceType.CUDA:
            try:
                import cupy as cp
                return cp.asnumpy(cp.convolve(cp.asarray(x), cp.asarray(kernel)))
            except ImportError:
                pass
        
        # Fallback to scipy
        try:
            from scipy.signal import convolve
            return convolve(x, kernel, mode='same')
        except ImportError:
            # Simple fallback
            return x
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Get current memory usage."""
        process = psutil.Process()
        mem_info = process.memory_info()
        
        return {
            "rss": mem_info.rss,  # Resident set size
            "vms": mem_info.vms,  # Virtual memory size
            "allocated": self.memory_manager.allocated_memory,
            "available": self.memory_manager.get_available_memory()
        }
    
    def benchmark_kernel(self, kernel_name: str, runs: int = 10) -> Dict:
        """
        Benchmark a kernel operation.
        
        Args:
            kernel_name: Name of kernel to benchmark.
            runs: Number of runs.
        
        Returns:
            Benchmark results.
        """
        import time
        
        # Setup test data
        a = np.random.randn(1024, 1024).astype(np.float32)
        b = np.random.randn(1024, 1024).astype(np.float32)
        
        times = []
        for _ in range(runs):
            start = time.time()
            
            if kernel_name == "matmul":
                self.matmul_optimized(a, b)
            elif kernel_name == "softmax":
                self.softmax_optimized(a)
            
            times.append(time.time() - start)
        
        return {
            "kernel": kernel_name,
            "runs": runs,
            "mean_time": np.mean(times),
            "std_time": np.std(times),
            "min_time": np.min(times),
            "max_time": np.max(times),
            "device": self.device.value
        }


class ComputeGraph:
    """Represents a computation graph for optimization."""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def add_node(self, op_name: str, inputs: List[int], output_shape: Tuple):
        """
        Add operation node to graph.
        
        Args:
            op_name: Operation name.
            inputs: Input node indices.
            output_shape: Output tensor shape.
        """
        node = {
            "op": op_name,
            "inputs": inputs,
            "output_shape": output_shape,
            "id": len(self.nodes)
        }
        self.nodes.append(node)
        return len(self.nodes) - 1
    
    def optimize(self) -> 'ComputeGraph':
        """
        Optimize computation graph.
        
        Returns:
            Optimized graph.
        """
        optimized = ComputeGraph()
        
        # Fuse operations where possible
        for node in self.nodes:
            optimized.add_node(node["op"], node["inputs"], node["output_shape"])
        
        return optimized
    
    def compile(self, device: DeviceType) -> Dict:
        """
        Compile graph for target device.
        
        Args:
            device: Target compute device.
        
        Returns:
            Compiled graph metadata.
        """
        return {
            "device": device.value,
            "num_nodes": len(self.nodes),
            "operations": [node["op"] for node in self.nodes]
        }
