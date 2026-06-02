"""
Inference Engine Module
Handles model loading, inference, and GPU/CPU management
"""

import numpy as np
import pickle
import os
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import json


@dataclass
class ModelConfig:
    """Configuration for a neural network model."""
    vocab_size: int
    embedding_dim: int
    hidden_dim: int
    num_layers: int
    num_heads: int
    max_seq_length: int
    dropout_rate: float = 0.1
    activation: str = "relu"


class ModelWeights:
    """Manages model weights and parameters."""
    
    def __init__(self):
        self.weights = {}
        self.device = self._detect_device()
    
    def _detect_device(self) -> str:
        """Detect available hardware."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():  # Apple Silicon
                return "mps"
        except ImportError:
            pass
        return "cpu"
    
    def save_weight(self, name: str, data: np.ndarray):
        """Save a weight tensor."""
        self.weights[name] = data.astype(np.float32)
    
    def load_weight(self, name: str) -> np.ndarray:
        """Load a weight tensor."""
        return self.weights.get(name, None)
    
    def to_device(self, data: np.ndarray) -> np.ndarray:
        """Move data to appropriate device."""
        if self.device == "cuda":
            # Would use torch/cupy here in production
            return data
        elif self.device == "mps":
            return data
        return data  # CPU
    
    def save_checkpoint(self, filepath: str, config: ModelConfig):
        """Save weights and config to file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        checkpoint = {
            "weights": self.weights,
            "config": {
                "vocab_size": config.vocab_size,
                "embedding_dim": config.embedding_dim,
                "hidden_dim": config.hidden_dim,
                "num_layers": config.num_layers,
                "num_heads": config.num_heads,
                "max_seq_length": config.max_seq_length,
                "dropout_rate": config.dropout_rate,
                "activation": config.activation,
            },
            "device": self.device
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(checkpoint, f)
    
    def load_checkpoint(self, filepath: str) -> ModelConfig:
        """Load weights and config from file."""
        with open(filepath, 'rb') as f:
            checkpoint = pickle.load(f)
        
        self.weights = checkpoint["weights"]
        self.device = checkpoint.get("device", "cpu")
        
        config_dict = checkpoint["config"]
        return ModelConfig(**config_dict)
    
    def get_weight_stats(self) -> Dict:
        """Get statistics about weights."""
        stats = {}
        for name, weight in self.weights.items():
            stats[name] = {
                "shape": weight.shape,
                "dtype": str(weight.dtype),
                "mean": float(np.mean(weight)),
                "std": float(np.std(weight)),
                "min": float(np.min(weight)),
                "max": float(np.max(weight)),
            }
        return stats
    
    def quantize(self, bits: int = 8) -> 'ModelWeights':
        """Quantize weights to lower precision."""
        quantized = ModelWeights()
        
        for name, weight in self.weights.items():
            if bits == 8:
                # int8 quantization
                min_val = np.min(weight)
                max_val = np.max(weight)
                scale = (max_val - min_val) / 255
                quantized_data = ((weight - min_val) / scale).astype(np.int8)
                quantized.weights[name] = quantized_data
            elif bits == 16:
                # float16 quantization
                quantized.weights[name] = weight.astype(np.float16)
        
        return quantized


class ModelLoader:
    """Loads pre-trained models in various formats."""
    
    @staticmethod
    def from_checkpoint(checkpoint_path: str) -> Tuple[ModelConfig, ModelWeights]:
        """
        Load model from checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file.
        
        Returns:
            Tuple of (config, weights).
        """
        weights = ModelWeights()
        config = weights.load_checkpoint(checkpoint_path)
        return config, weights
    
    @staticmethod
    def from_onnx(onnx_path: str) -> Dict:
        """
        Load model from ONNX format.
        
        Args:
            onnx_path: Path to ONNX file.
        
        Returns:
            Model metadata.
        """
        # ONNX loading would be implemented with onnxruntime
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(onnx_path)
            return {
                "inputs": [inp.name for inp in session.get_inputs()],
                "outputs": [out.name for out in session.get_outputs()],
                "session": session
            }
        except ImportError:
            return {"error": "onnxruntime not installed"}
    
    @staticmethod
    def from_safetensors(safetensors_path: str) -> ModelWeights:
        """
        Load model from SafeTensors format.
        
        Args:
            safetensors_path: Path to SafeTensors file.
        
        Returns:
            Model weights.
        """
        try:
            from safetensors.numpy import load_file
            data = load_file(safetensors_path)
            
            weights = ModelWeights()
            for name, tensor in data.items():
                weights.save_weight(name, tensor)
            return weights
        except ImportError:
            return None


class InferenceEngine:
    """Main inference engine for running models."""
    
    def __init__(self, config: ModelConfig, weights: ModelWeights):
        """
        Initialize inference engine.
        
        Args:
            config: Model configuration.
            weights: Model weights.
        """
        self.config = config
        self.weights = weights
        self.device = weights.device
        self.cache = {}  # KV cache for attention
    
    def prepare_input(self, token_ids: List[int]) -> np.ndarray:
        """
        Prepare input tokens for inference.
        
        Args:
            token_ids: List of token IDs.
        
        Returns:
            Processed input tensor.
        """
        # Pad or truncate to max_seq_length
        seq_len = len(token_ids)
        if seq_len > self.config.max_seq_length:
            token_ids = token_ids[:self.config.max_seq_length]
        elif seq_len < self.config.max_seq_length:
            token_ids = token_ids + [0] * (self.config.max_seq_length - seq_len)
        
        # Convert to numpy array
        input_array = np.array([token_ids], dtype=np.int32)
        return self.weights.to_device(input_array)
    
    def forward(self, token_ids: List[int]) -> np.ndarray:
        """
        Run forward pass on input tokens.
        
        Args:
            token_ids: List of token IDs.
        
        Returns:
            Output logits.
        """
        input_tensor = self.prepare_input(token_ids)
        
        # Simple forward pass (simplified - real implementation would use layers)
        batch_size = input_tensor.shape[0]
        seq_len = input_tensor.shape[1]
        
        # Embed tokens
        embedding_matrix = self.weights.load_weight("embedding.weight")
        if embedding_matrix is not None:
            embeddings = embedding_matrix[input_tensor[0]]
        else:
            # Initialize random embeddings if not loaded
            embeddings = np.random.randn(seq_len, self.config.embedding_dim).astype(np.float32)
        
        # Simple transformer block
        hidden = embeddings
        
        # Apply attention layers (simplified)
        for layer_id in range(self.config.num_layers):
            # Would apply attention and feed-forward here
            pass
        
        # Project to vocabulary
        output_weight = self.weights.load_weight("output.weight")
        if output_weight is not None:
            logits = hidden @ output_weight
        else:
            logits = np.random.randn(seq_len, self.config.vocab_size).astype(np.float32)
        
        return logits
    
    def generate(self, prompt_ids: List[int], max_tokens: int = 50, temperature: float = 0.7) -> List[int]:
        """
        Generate tokens using the model.
        
        Args:
            prompt_ids: Initial prompt token IDs.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature (higher = more random).
        
        Returns:
            Generated token IDs.
        """
        generated = prompt_ids.copy()
        
        for _ in range(max_tokens):
            # Get logits for next token
            logits = self.forward(generated)
            
            # Get logits for last token
            next_logits = logits[-1, :]
            
            # Apply temperature
            next_logits = next_logits / temperature
            
            # Compute probabilities
            probs = self._softmax(next_logits)
            
            # Sample next token
            next_token = np.random.choice(
                np.arange(len(probs)), 
                p=probs
            )
            
            generated.append(int(next_token))
            
            # Stop if EOS token generated
            if next_token == 0:
                break
        
        return generated
    
    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Compute softmax."""
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / np.sum(exp_logits)
    
    def clear_cache(self):
        """Clear KV cache."""
        self.cache = {}
    
    def benchmark(self, num_tokens: int = 100) -> Dict:
        """
        Benchmark inference speed.
        
        Args:
            num_tokens: Number of tokens to generate.
        
        Returns:
            Benchmark results.
        """
        import time
        
        start = time.time()
        token_ids = list(range(min(10, self.config.vocab_size)))
        _ = self.generate(token_ids, max_tokens=num_tokens)
        elapsed = time.time() - start
        
        return {
            "tokens_generated": num_tokens,
            "time_seconds": elapsed,
            "tokens_per_second": num_tokens / elapsed,
            "device": self.device
        }
