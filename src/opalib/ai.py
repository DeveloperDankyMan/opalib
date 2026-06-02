"""
Simplified AI Module - Uses Ollama or Pollinations
"""

import random
import requests
from typing import List, Dict, Optional

# Try to import Ollama, fall back to Pollinations
try:
    from src.opalib.ollama_integration import OllamaClient, OllamaAgent
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


def ask_ai(prompt: str, act_as: str = "A helpful and accurate assistant.",
           use_ollama: bool = True) -> str:
    """
    Query AI with automatic Ollama/Pollinations fallback.
    
    Args:
        prompt: Main request or question.
        act_as: System persona/instructions.
        use_ollama: Prefer Ollama if available.
    
    Returns:
        AI response.
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string.")
    
    # Try Ollama first
    if use_ollama and OLLAMA_AVAILABLE:
        try:
            client = OllamaClient()
            messages = [
                {"role": "system", "content": act_as},
                {"role": "user", "content": prompt}
            ]
            return client.chat(messages)
        except Exception as e:
            print(f"Ollama failed: {e}. Falling back to Pollinations...")
    
    # Fall back to Pollinations (free cloud API)
    return _ask_pollinations(prompt, act_as)


def _ask_pollinations(prompt: str, act_as: str) -> str:
    """
    Query Pollinations AI (free, no API key required).
    
    Args:
        prompt: Input prompt.
        act_as: System instructions.
    
    Returns:
        Response text.
    """
    url = "https://text.pollinations.ai"
    
    payload = {
        "messages": [
            {"role": "system", "content": act_as},
            {"role": "user", "content": prompt}
        ],
        "model": "openai",
        "seed": random.randint(1, 99999999),
        "jsonMode": False,
        "private": True
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"Error: Server returned status code {response.status_code}"
    
    except requests.exceptions.Timeout:
        return "Error: The connection timed out."
    except requests.exceptions.RequestException as e:
        return f"Error: Network problem encountered. Details: {e}"


def create_ollama_agent(name: str, model: str = "mistral",
                       system_prompt: str = None) -> Optional[OllamaAgent]:
    """
    Create an Ollama-powered agent.
    
    Args:
        name: Agent name.
        model: Ollama model to use.
        system_prompt: System instructions.
    
    Returns:
        OllamaAgent or None if Ollama unavailable.
    """
    if not OLLAMA_AVAILABLE:
        print("Ollama not available. Install with: pip install ollama")
        return None
    
    return OllamaAgent(name, model, system_prompt)


def create_hybrid_agent(name: str, prefer_ollama: bool = True,
                       ollama_model: str = "mistral",
                       system_prompt: str = None):
    """
    Create an agent that uses Ollama if available, falls back to Pollinations.
    
    Args:
        name: Agent name.
        prefer_ollama: Prefer Ollama over Pollinations.
        ollama_model: Ollama model if using it.
        system_prompt: System instructions.
    
    Returns:
        HybridAgent wrapper.
    """
    return HybridAgent(name, prefer_ollama, ollama_model, system_prompt)


class HybridAgent:
    """Agent that uses Ollama or Pollinations based on availability."""
    
    def __init__(self, name: str, prefer_ollama: bool = True,
                 ollama_model: str = "mistral",
                 system_prompt: str = None):
        self.name = name
        self.prefer_ollama = prefer_ollama
        self.ollama_model = ollama_model
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.conversation_history = []
        self.using_ollama = False
        
        # Try to use Ollama
        if prefer_ollama and OLLAMA_AVAILABLE:
            try:
                self.ollama_agent = OllamaAgent(
                    name, ollama_model, system_prompt
                )
                self.using_ollama = True
            except:
                self.using_ollama = False
    
    def chat(self, message: str) -> str:
        """
        Chat with hybrid agent.
        
        Args:
            message: User message.
        
        Returns:
            Agent response.
        """
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        if self.using_ollama:
            response = self.ollama_agent.chat(message)
        else:
            # Use Pollinations
            response = _ask_pollinations(message, self.system_prompt)
        
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
    
    def switch_backend(self, use_ollama: bool = None):
        """
        Switch between Ollama and Pollinations.
        
        Args:
            use_ollama: True for Ollama, False for Pollinations.
        """
        if use_ollama and OLLAMA_AVAILABLE and not self.using_ollama:
            self.ollama_agent = OllamaAgent(
                self.name, self.ollama_model, self.system_prompt
            )
            self.using_ollama = True
        elif not use_ollama:
            self.using_ollama = False
