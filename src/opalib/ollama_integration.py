"""
Ollama Integration Module
Provides seamless integration with Ollama for local model inference
Supports both Ollama Python client and REST API
"""

import requests
import json
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import subprocess
import time
import os
import platform


@dataclass
class OllamaConfig:
    """Configuration for Ollama connection."""
    host: str = "http://localhost"
    port: int = 11434
    model: str = "mistral"
    timeout: int = 300
    auto_start: bool = True


class OllamaClient:
    """
    Client for interacting with Ollama server.
    Works with Ollama Python library or direct HTTP API.
    """
    
    def __init__(self, config: OllamaConfig = None):
        """
        Initialize Ollama client.
        
        Args:
            config: Ollama configuration.
        """
        self.config = config or OllamaConfig()
        self.base_url = f"{self.config.host}:{self.config.port}"
        self.available_models = []
        self.current_model = self.config.model
        
        # Try to use ollama-python library first
        self.use_python_lib = self._try_import_ollama()
        
        if not self.use_python_lib:
            # Fall back to REST API
            self._ensure_server_running()
        
        self._load_available_models()
    
    def _try_import_ollama(self) -> bool:
        """Try to import and use ollama-python library."""
        try:
            import ollama
            self.ollama_lib = ollama
            return True
        except ImportError:
            return False
    
    def _ensure_server_running(self) -> bool:
        """
        Ensure Ollama server is running.
        
        Returns:
            True if server is running or started successfully.
        """
        if self._check_server_health():
            return True
        
        if not self.config.auto_start:
            raise ConnectionError(
                f"Ollama server not running at {self.base_url}. "
                "Set auto_start=True or start server manually."
            )
        
        print(f"Starting Ollama server at {self.base_url}...")
        return self._start_ollama_server()
    
    def _check_server_health(self) -> bool:
        """Check if Ollama server is responding."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _start_ollama_server(self) -> bool:
        """Start Ollama server as subprocess."""
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: use wsl or native
                cmd = ["ollama", "serve"]
            elif system == "Darwin":
                # macOS: use native
                cmd = ["ollama", "serve"]
            else:
                # Linux
                cmd = ["ollama", "serve"]
            
            # Start server in background
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for attempt in range(30):
                time.sleep(1)
                if self._check_server_health():
                    print("Ollama server started successfully!")
                    return True
            
            return False
        except Exception as e:
            print(f"Failed to start Ollama server: {e}")
            return False
    
    def _load_available_models(self):
        """Load list of available models from Ollama."""
        try:
            if self.use_python_lib:
                # Use Python library
                response = self.ollama_lib.list()
                self.available_models = [m['name'].split(':')[0] for m in response.get('models', [])]
            else:
                # Use REST API
                response = requests.get(
                    f"{self.base_url}/api/tags",
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    data = response.json()
                    self.available_models = [
                        m['name'].split(':')[0] for m in data.get('models', [])
                    ]
        except Exception as e:
            print(f"Warning: Could not load available models: {e}")
            self.available_models = []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Download a model from Ollama Hub.
        
        Args:
            model_name: Name of model to pull (e.g., "mistral", "neural-chat").
        
        Returns:
            True if successful.
        """
        try:
            print(f"Pulling model: {model_name}...")
            
            if self.use_python_lib:
                # Use Python library
                self.ollama_lib.pull(model_name)
            else:
                # Use REST API
                response = requests.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name},
                    stream=True,
                    timeout=None
                )
                
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if 'status' in data:
                            print(f"  {data['status']}")
            
            self.current_model = model_name
            self._load_available_models()
            print(f"Successfully pulled {model_name}")
            return True
        
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False
    
    def generate(self, prompt: str, stream: bool = False) -> Union[str, List[str]]:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input prompt.
            stream: Whether to stream response.
        
        Returns:
            Generated text or stream of responses.
        """
        try:
            if self.use_python_lib:
                # Use Python library
                response = self.ollama_lib.generate(
                    model=self.current_model,
                    prompt=prompt,
                    stream=stream
                )
                
                if stream:
                    responses = []
                    for chunk in response:
                        responses.append(chunk['response'])
                    return responses
                else:
                    return response['response']
            else:
                # Use REST API
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.current_model,
                        "prompt": prompt,
                        "stream": stream
                    },
                    stream=stream,
                    timeout=self.config.timeout
                )
                
                if stream:
                    responses = []
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            responses.append(data.get('response', ''))
                    return responses
                else:
                    data = response.json()
                    return data.get('response', '')
        
        except Exception as e:
            print(f"Error generating text: {e}")
            return ""
    
    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Union[str, List[str]]:
        """
        Chat with a model using conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            stream: Whether to stream response.
        
        Returns:
            Generated response or stream.
        """
        try:
            if self.use_python_lib:
                # Use Python library
                response = self.ollama_lib.chat(
                    model=self.current_model,
                    messages=messages,
                    stream=stream
                )
                
                if stream:
                    responses = []
                    for chunk in response:
                        responses.append(chunk['message']['content'])
                    return responses
                else:
                    return response['message']['content']
            else:
                # Use REST API
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.current_model,
                        "messages": messages,
                        "stream": stream
                    },
                    stream=stream,
                    timeout=self.config.timeout
                )
                
                if stream:
                    responses = []
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            responses.append(data.get('message', {}).get('content', ''))
                    return responses
                else:
                    data = response.json()
                    return data.get('message', {}).get('content', '')
        
        except Exception as e:
            print(f"Error in chat: {e}")
            return ""
    
    def set_model(self, model_name: str):
        """
        Switch to a different model.
        
        Args:
            model_name: Name of model to use.
        """
        self.current_model = model_name
    
    def list_models(self) -> List[str]:
        """Get list of available models."""
        return self.available_models
    
    def get_model_info(self, model_name: str = None) -> Dict:
        """
        Get information about a model.
        
        Args:
            model_name: Model to get info for (uses current if not specified).
        
        Returns:
            Model information.
        """
        model_name = model_name or self.current_model
        
        try:
            if self.use_python_lib:
                info = self.ollama_lib.show(model_name)
                return info
            else:
                response = requests.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name},
                    timeout=self.config.timeout
                )
                return response.json()
        except Exception as e:
            print(f"Error getting model info: {e}")
            return {}


class OllamaAgent:
    """AI Agent powered by Ollama."""
    
    def __init__(self, name: str, model: str = "mistral", 
                 system_prompt: str = None, config: OllamaConfig = None):
        """
        Initialize Ollama-based agent.
        
        Args:
            name: Agent name.
            model: Ollama model to use.
            system_prompt: System instructions.
            config: Ollama configuration.
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.conversation_history = []
        self.client = OllamaClient(config)
        self.client.set_model(model)
    
    def chat(self, message: str, stream: bool = False) -> Union[str, List[str]]:
        """
        Chat with the agent.
        
        Args:
            message: User message.
            stream: Whether to stream response.
        
        Returns:
            Agent response.
        """
        # Add to history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        # Build message list with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        messages.extend(self.conversation_history[-10:])  # Last 10 messages
        
        # Get response
        response = self.client.chat(messages, stream=stream)
        
        # Handle streaming
        if isinstance(response, list):
            full_response = "".join(response)
        else:
            full_response = response
        
        # Add to history
        self.conversation_history.append({
            "role": "assistant",
            "content": full_response
        })
        
        return full_response
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.conversation_history


class OllamaMultiAgent:
    """Multiple agents using Ollama."""
    
    def __init__(self, agents_config: List[Dict], config: OllamaConfig = None):
        """
        Initialize multiple Ollama agents.
        
        Args:
            agents_config: List of agent configs (name, model, system_prompt).
            config: Ollama configuration.
        """
        self.agents = {}
        self.config = config or OllamaConfig()
        self.conversation_log = []
        
        for agent_cfg in agents_config:
            agent = OllamaAgent(
                name=agent_cfg['name'],
                model=agent_cfg.get('model', 'mistral'),
                system_prompt=agent_cfg.get('system_prompt'),
                config=self.config
            )
            self.agents[agent_cfg['name']] = agent
    
    def start_conversation(self, topic: str, max_turns: int = 5) -> List[Dict]:
        """
        Start a conversation between agents.
        
        Args:
            topic: Topic to discuss.
            max_turns: Number of turns.
        
        Returns:
            Conversation log.
        """
        self.conversation_log = []
        agents_list = list(self.agents.values())
        
        # First agent starts
        first_agent = agents_list[0]
        response = first_agent.chat(f"Let's discuss: {topic}")
        
        self.conversation_log.append({
            "agent": first_agent.name,
            "message": response
        })
        
        print(f"[{first_agent.name}]: {response}\n")
        
        # Back and forth
        for turn in range(max_turns):
            for i, agent in enumerate(agents_list):
                if i == 0 and turn == 0:
                    continue
                
                # Get context from last message
                last_message = self.conversation_log[-1]['message']
                context = f"Respond to this: {last_message}"
                
                response = agent.chat(context)
                
                self.conversation_log.append({
                    "agent": agent.name,
                    "message": response
                })
                
                print(f"[{agent.name}]: {response}\n")
        
        return self.conversation_log
    
    def get_agent(self, name: str) -> OllamaAgent:
        """Get agent by name."""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all agents."""
        return list(self.agents.keys())
