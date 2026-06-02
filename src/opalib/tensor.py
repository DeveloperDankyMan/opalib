"""
Tensor Framework Module
Implements basic tensor operations (matrix math, activations, etc.)
"""

import numpy as np
from typing import List, Tuple, Union, Optional
from dataclasses import dataclass


class Tensor:
    """
    Basic tensor class for neural network operations.
    Wraps NumPy arrays with automatic differentiation support.
    """
    
    def __init__(self, data: Union[np.ndarray, list, float], requires_grad: bool = False):
        """
        Initialize a tensor.
        
        Args:
            data: Input data (array, list, or scalar).
            requires_grad: Whether to track gradients.
        """
        if isinstance(data, (list, float, int)):
            self.data = np.array(data, dtype=np.float32)
        else:
            self.data = np.array(data, dtype=np.float32)
        
        self.requires_grad = requires_grad
        self.grad = None
        self.grad_fn = None
    
    @property
    def shape(self) -> Tuple:
        """Get tensor shape."""
        return self.data.shape
    
    @property
    def size(self) -> int:
        """Get total number of elements."""
        return self.data.size
    
    def reshape(self, *shape) -> 'Tensor':
        """Reshape tensor."""
        return Tensor(self.data.reshape(shape), requires_grad=self.requires_grad)
    
    def transpose(self) -> 'Tensor':
        """Transpose tensor."""
        return Tensor(self.data.T, requires_grad=self.requires_grad)
    
    def __add__(self, other: Union['Tensor', float]) -> 'Tensor':
        """Element-wise addition."""
        if isinstance(other, Tensor):
            result_data = self.data + other.data
        else:
            result_data = self.data + other
        
        return Tensor(result_data, requires_grad=self.requires_grad or (isinstance(other, Tensor) and other.requires_grad))
    
    def __sub__(self, other: Union['Tensor', float]) -> 'Tensor':
        """Element-wise subtraction."""
        if isinstance(other, Tensor):
            result_data = self.data - other.data
        else:
            result_data = self.data - other
        
        return Tensor(result_data, requires_grad=self.requires_grad or (isinstance(other, Tensor) and other.requires_grad))
    
    def __mul__(self, other: Union['Tensor', float]) -> 'Tensor':
        """Element-wise multiplication."""
        if isinstance(other, Tensor):
            result_data = self.data * other.data
        else:
            result_data = self.data * other
        
        return Tensor(result_data, requires_grad=self.requires_grad or (isinstance(other, Tensor) and other.requires_grad))
    
    def __truediv__(self, other: Union['Tensor', float]) -> 'Tensor':
        """Element-wise division."""
        if isinstance(other, Tensor):
            result_data = self.data / other.data
        else:
            result_data = self.data / other
        
        return Tensor(result_data, requires_grad=self.requires_grad or (isinstance(other, Tensor) and other.requires_grad))
    
    def __matmul__(self, other: 'Tensor') -> 'Tensor':
        """Matrix multiplication."""
        result_data = np.matmul(self.data, other.data)
        return Tensor(result_data, requires_grad=self.requires_grad or other.requires_grad)
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __rsub__(self, other):
        return Tensor(other) - self
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def sum(self, axis: Optional[int] = None, keepdims: bool = False) -> 'Tensor':
        """Sum tensor elements."""
        return Tensor(np.sum(self.data, axis=axis, keepdims=keepdims), requires_grad=self.requires_grad)
    
    def mean(self, axis: Optional[int] = None, keepdims: bool = False) -> 'Tensor':
        """Mean of tensor elements."""
        return Tensor(np.mean(self.data, axis=axis, keepdims=keepdims), requires_grad=self.requires_grad)
    
    def softmax(self, axis: int = -1) -> 'Tensor':
        """Softmax activation."""
        exp_data = np.exp(self.data - np.max(self.data, axis=axis, keepdims=True))
        softmax_data = exp_data / np.sum(exp_data, axis=axis, keepdims=True)
        return Tensor(softmax_data, requires_grad=self.requires_grad)
    
    def relu(self) -> 'Tensor':
        """ReLU activation."""
        return Tensor(np.maximum(self.data, 0), requires_grad=self.requires_grad)
    
    def tanh(self) -> 'Tensor':
        """Tanh activation."""
        return Tensor(np.tanh(self.data), requires_grad=self.requires_grad)
    
    def sigmoid(self) -> 'Tensor':
        """Sigmoid activation."""
        return Tensor(1 / (1 + np.exp(-self.data)), requires_grad=self.requires_grad)
    
    def log(self) -> 'Tensor':
        """Natural logarithm."""
        return Tensor(np.log(self.data + 1e-8), requires_grad=self.requires_grad)
    
    def exp(self) -> 'Tensor':
        """Exponential."""
        return Tensor(np.exp(self.data), requires_grad=self.requires_grad)
    
    def clip(self, min_val: float = 0, max_val: float = 1) -> 'Tensor':
        """Clip values to range."""
        return Tensor(np.clip(self.data, min_val, max_val), requires_grad=self.requires_grad)
    
    def __repr__(self) -> str:
        return f"Tensor({self.data}, requires_grad={self.requires_grad})"


class Linear:
    """Linear (fully connected) layer."""
    
    def __init__(self, in_features: int, out_features: int):
        """
        Initialize linear layer.
        
        Args:
            in_features: Size of input features.
            out_features: Size of output features.
        """
        # Xavier initialization
        limit = np.sqrt(6.0 / (in_features + out_features))
        self.weight = Tensor(
            np.random.uniform(-limit, limit, (in_features, out_features)),
            requires_grad=True
        )
        self.bias = Tensor(np.zeros(out_features), requires_grad=True)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, in_features).
        
        Returns:
            Output tensor of shape (batch_size, out_features).
        """
        return x @ self.weight + self.bias
    
    def __call__(self, x: Tensor) -> Tensor:
        return self.forward(x)


class Embedding:
    """Embedding layer for token encoding."""
    
    def __init__(self, vocab_size: int, embedding_dim: int):
        """
        Initialize embedding layer.
        
        Args:
            vocab_size: Size of vocabulary.
            embedding_dim: Dimension of embeddings.
        """
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        # Initialize embeddings randomly
        self.weight = Tensor(
            np.random.normal(0, 0.02, (vocab_size, embedding_dim)),
            requires_grad=True
        )
    
    def forward(self, token_ids: np.ndarray) -> Tensor:
        """
        Forward pass.
        
        Args:
            token_ids: Array of token indices.
        
        Returns:
            Embedding tensor.
        """
        return Tensor(self.weight.data[token_ids.flatten()], requires_grad=self.weight.requires_grad)
    
    def __call__(self, token_ids: np.ndarray) -> Tensor:
        return self.forward(token_ids)


class Attention:
    """Multi-head attention mechanism."""
    
    def __init__(self, dim: int, num_heads: int = 8):
        """
        Initialize attention layer.
        
        Args:
            dim: Dimension of attention.
            num_heads: Number of attention heads.
        """
        assert dim % num_heads == 0
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        
        self.query = Linear(dim, dim)
        self.key = Linear(dim, dim)
        self.value = Linear(dim, dim)
        self.output = Linear(dim, dim)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor.
        
        Returns:
            Attention output.
        """
        batch_size = x.shape[0]
        seq_len = x.shape[1]
        
        # Project to Q, K, V
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)
        
        # Reshape for multi-head attention
        Q = Q.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        K = K.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        V = V.reshape(batch_size, seq_len, self.num_heads, self.head_dim)
        
        # Compute attention scores
        scores = Q @ K.transpose() / np.sqrt(self.head_dim)
        attention_weights = scores.softmax(axis=-1)
        
        # Apply attention to values
        context = attention_weights @ V
        
        # Reshape and output
        context = context.reshape(batch_size, seq_len, self.dim)
        output = self.output(context)
        
        return output
    
    def __call__(self, x: Tensor) -> Tensor:
        return self.forward(x)


class LayerNorm:
    """Layer normalization."""
    
    def __init__(self, dim: int, eps: float = 1e-6):
        """
        Initialize layer norm.
        
        Args:
            dim: Dimension to normalize.
            eps: Small value for numerical stability.
        """
        self.dim = dim
        self.eps = eps
        self.gamma = Tensor(np.ones(dim), requires_grad=True)
        self.beta = Tensor(np.zeros(dim), requires_grad=True)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor.
        
        Returns:
            Normalized tensor.
        """
        mean = x.mean(axis=-1, keepdims=True)
        std = np.std(x.data, axis=-1, keepdims=True)
        normalized = (x - mean) / (Tensor(std) + self.eps)
        return normalized * self.gamma + self.beta
    
    def __call__(self, x: Tensor) -> Tensor:
        return self.forward(x)
