"""
Unified AI Framework Integration
Combines tokenizer, tensor, inference, and hardware into one system
"""

from typing import List, Dict, Optional, Union
import numpy as np
from dataclasses import dataclass
import json
import os

# Import components
from .tokenizer import BPETokenizer, SimpleTokenizer
from .tensor import Tensor, Linear, Embedding, Attention, LayerNorm
from .inference import ModelConfig, ModelWeights, InferenceEngine, ModelLoader
from .hardware import HardwareAccelerator, DeviceType, MemoryManager, ComputeGraph


@dataclass
class LocalModelConfig:
    """Configuration for local AI models."""
    name: str
    model_type: str  # "transformer", "lstm", "gpt2", etc.
    vocab_size: int
    embedding_dim: int
    hidden_dim: int
    num_layers: int
    num_heads: int
    max_seq_length: int
    device: str = "cpu"
    use_quantization: bool = False
    quantization_bits: int = 8


class LocalAIModel:
    """Complete local AI model with all components."""
    
    def __init__(self, config: LocalModelConfig):
        """
        Initialize local AI model.
        
        Args:
            config: Model configuration.
        """
        self.config = config
        self.tokenizer = BPETokenizer(vocab_size=config.vocab_size)
        
        # Setup hardware
        device_map = {
            "cpu": DeviceType.CPU,
            "cuda": DeviceType.CUDA,
            "mps": DeviceType.MPS,
        }
        device = device_map.get(config.device, DeviceType.CPU)
        self.accelerator = HardwareAccelerator(device)
        
        # Setup model
        self.model_config = ModelConfig(
            vocab_size=config.vocab_size,
            embedding_dim=config.embedding_dim,
            hidden_dim=config.hidden_dim,
            num_layers=config.num_layers,
            num_heads=config.num_heads,
            max_seq_length=config.max_seq_length
        )
        self.weights = ModelWeights()
        self.inference_engine = InferenceEngine(self.model_config, self.weights)
        
        # Optional quantization
        if config.use_quantization:
            self.quantize(config.quantization_bits)
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text.
        
        Returns:
            Token IDs.
        """
        return self.tokenizer.encode(text)
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: Token IDs to decode.
        
        Returns:
            Decoded text.
        """
        return self.tokenizer.decode(token_ids)
    
    def generate(self, prompt: str, max_tokens: int = 50, temperature: float = 0.7) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
        
        Returns:
            Generated text.
        """
        # Encode prompt
        prompt_ids = self.encode(prompt)
        
        # Generate tokens
        generated_ids = self.inference_engine.generate(
            prompt_ids,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Decode back to text
        generated_text = self.decode(generated_ids)
        return generated_text
    
    def quantize(self, bits: int = 8):
        """
        Quantize model weights.
        
        Args:
            bits: Quantization bits (8 or 16).
        """
        self.weights = self.weights.quantize(bits)
    
    def save(self, filepath: str):
        """
        Save model to disk.
        
        Args:
            filepath: Path to save model.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save config
        config_path = filepath.replace('.pt', '_config.json')
        with open(config_path, 'w') as f:
            json.dump({
                "name": self.config.name,
                "model_type": self.config.model_type,
                "vocab_size": self.config.vocab_size,
                "embedding_dim": self.config.embedding_dim,
                "hidden_dim": self.config.hidden_dim,
                "num_layers": self.config.num_layers,
                "num_heads": self.config.num_heads,
                "max_seq_length": self.config.max_seq_length,
            }, f)
        
        # Save weights
        self.weights.save_checkpoint(filepath, self.model_config)
        
        # Save tokenizer
        tokenizer_path = filepath.replace('.pt', '_tokenizer.json')
        self.tokenizer.save(tokenizer_path)
    
    @classmethod
    def load(cls, filepath: str) -> 'LocalAIModel':
        """
        Load model from disk.
        
        Args:
            filepath: Path to load model.
        
        Returns:
            Loaded model.
        """
        # Load config
        config_path = filepath.replace('.pt', '_config.json')
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        # Create config
        config = LocalModelConfig(**config_dict)
        
        # Create model
        model = cls(config)
        
        # Load weights
        model.weights.load_checkpoint(filepath)
        
        # Load tokenizer
        tokenizer_path = filepath.replace('.pt', '_tokenizer.json')
        model.tokenizer.load(tokenizer_path)
        
        return model
    
    def get_stats(self) -> Dict:
        """Get model statistics."""
        return {
            "config": {
                "name": self.config.name,
                "vocab_size": self.config.vocab_size,
                "embedding_dim": self.config.embedding_dim,
                "hidden_dim": self.config.hidden_dim,
                "num_layers": self.config.num_layers,
                "num_heads": self.config.num_heads,
            },
            "device": self.config.device,
            "memory_usage": self.accelerator.get_memory_usage(),
            "weight_stats": self.weights.get_weight_stats(),
        }
    
    def benchmark(self, num_tokens: int = 100) -> Dict:
        """
        Benchmark model performance.
        
        Args:
            num_tokens: Tokens to generate for benchmark.
        
        Returns:
            Benchmark results.
        """
        return self.inference_engine.benchmark(num_tokens)


class UnifiedAIFramework:
    """
    Unified framework for creating and managing local AI agents.
    Combines all components into simple API.
    """
    
    def __init__(self, device: str = "auto"):
        """
        Initialize framework.
        
        Args:
            device: Compute device ("cpu", "cuda", "mps", or "auto").
        """
        if device == "auto":
            self.device = HardwareAccelerator.detect_device().value
        else:
            self.device = device
        
        self.models = {}
        self.agents = {}
        self.hardware = HardwareAccelerator(
            DeviceType[self.device.upper()] if self.device.upper() in DeviceType.__members__
            else DeviceType.CPU
        )
    
    def create_model(self, name: str, model_type: str = "transformer",
                     vocab_size: int = 5000, embedding_dim: int = 256,
                     hidden_dim: int = 512, num_layers: int = 4,
                     num_heads: int = 8, max_seq_length: int = 512) -> LocalAIModel:
        """
        Create a new local AI model.
        
        Args:
            name: Model name.
            model_type: Type of model architecture.
            vocab_size: Size of vocabulary.
            embedding_dim: Embedding dimension.
            hidden_dim: Hidden layer dimension.
            num_layers: Number of layers.
            num_heads: Number of attention heads.
            max_seq_length: Maximum sequence length.
        
        Returns:
            Created model.
        """
        config = LocalModelConfig(
            name=name,
            model_type=model_type,
            vocab_size=vocab_size,
            embedding_dim=embedding_dim,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            num_heads=num_heads,
            max_seq_length=max_seq_length,
            device=self.device
        )
        
        model = LocalAIModel(config)
        self.models[name] = model
        return model
    
    def create_agent(self, name: str, model_name: str, system_prompt: str = None) -> 'LocalAgent':
        """
        Create an AI agent with a model.
        
        Args:
            name: Agent name.
            model_name: Name of model to use.
            system_prompt: System instructions for agent.
        
        Returns:
            Created agent.
        """
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found. Available: {list(self.models.keys())}")
        
        agent = LocalAgent(name, self.models[model_name], system_prompt)
        self.agents[name] = agent
        return agent
    
    def get_model(self, name: str) -> LocalAIModel:
        """Get model by name."""
        return self.models.get(name)
    
    def get_agent(self, name: str) -> 'LocalAgent':
        """Get agent by name."""
        return self.agents.get(name)
    
    def list_models(self) -> List[str]:
        """List all available models."""
        return list(self.models.keys())
    
    def list_agents(self) -> List[str]:
        """List all available agents."""
        return list(self.agents.keys())


class LocalAgent:
    """An AI agent using a local model."""
    
    def __init__(self, name: str, model: LocalAIModel, system_prompt: str = None):
        """
        Initialize local agent.
        
        Args:
            name: Agent name.
            model: AI model to use.
            system_prompt: System instructions.
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.conversation_history = []
    
    def chat(self, message: str, max_tokens: int = 100) -> str:
        """
        Chat with agent.
        
        Args:
            message: User message.
            max_tokens: Max tokens to generate.
        
        Returns:
            Agent response.
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Format prompt with system and history
        full_prompt = self.system_prompt + "\n\n"
        for entry in self.conversation_history[-5:]:  # Last 5 messages for context
            full_prompt += f"{entry['role']}: {entry['content']}\n"
        
        # Generate response
        response = self.model.generate(full_prompt, max_tokens=max_tokens)
        
        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history
