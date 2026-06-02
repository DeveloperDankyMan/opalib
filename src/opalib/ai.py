import random
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Agent:
    """Represents an AI agent with its own personality and conversation history."""
    name: str
    system_prompt: str
    conversation_history: List[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
    
    def add_message(self, role: str, content: str):
        """Add a message to this agent's conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def clear_history(self):
        """Clear the conversation history for this agent."""
        self.conversation_history = []


class AgentConversation:
    """Manages conversations between multiple AI agents."""
    
    def __init__(self, agents: List[Agent], api_url: str = "https://text.pollinations.ai"):
        """
        Initialize a multi-agent conversation.
        
        Args:
            agents (List[Agent]): List of Agent objects to participate in conversation.
            api_url (str): The API endpoint URL for AI requests.
        """
        if not agents or len(agents) < 2:
            raise ValueError("At least 2 agents are required for a conversation.")
        
        self.agents = {agent.name: agent for agent in agents}
        self.api_url = api_url
        self.conversation_log = []
    
    def _query_agent(self, agent: Agent, user_input: str = "") -> str:
        """
        Query a single agent for a response.
        
        Args:
            agent (Agent): The agent to query.
            user_input (str): Optional context or message to include.
        
        Returns:
            str: The agent's response.
        """
        # Build messages: system prompt + history + current input
        messages = [{"role": "system", "content": agent.system_prompt}]
        messages.extend(agent.conversation_history)
        
        if user_input:
            messages.append({"role": "user", "content": user_input})
        
        payload = {
            "messages": messages,
            "model": "openai",
            "seed": random.randint(1, 99999999),
            "jsonMode": False,
            "private": True
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.text.strip()
            else:
                return f"Error: Server returned status code {response.status_code}"
        
        except requests.exceptions.Timeout:
            return "Error: Connection timed out."
        except requests.exceptions.RequestException as e:
            return f"Error: Network problem encountered. Details: {e}"
    
    def start_conversation(self, topic: str, max_turns: int = 5) -> List[Dict[str, str]]:
        """
        Start a conversation between agents on a given topic.
        
        Args:
            topic (str): The topic or initial prompt for the conversation.
            max_turns (int): Maximum number of back-and-forth exchanges.
        
        Returns:
            List[Dict[str, str]]: The complete conversation log.
        """
        self.conversation_log = []
        agent_list = list(self.agents.values())
        
        # First agent starts the conversation
        first_agent = agent_list[0]
        initial_response = self._query_agent(first_agent, f"Topic: {topic}")
        first_agent.add_message("assistant", initial_response)
        
        self.conversation_log.append({
            "timestamp": datetime.now().isoformat(),
            "agent": first_agent.name,
            "message": initial_response
        })
        
        # Back-and-forth conversation
        for turn in range(max_turns):
            for i, agent in enumerate(agent_list):
                if i == 0 and turn == 0:
                    continue  # Skip first agent on first turn (already spoke)
                
                # Get context from the last message
                if self.conversation_log:
                    context = f"Respond to: {self.conversation_log[-1]['message']}"
                else:
                    context = f"Topic: {topic}"
                
                response = self._query_agent(agent, context)
                agent.add_message("assistant", response)
                
                self.conversation_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "agent": agent.name,
                    "message": response
                })
        
        return self.conversation_log
    
    def get_conversation_log(self) -> List[Dict[str, str]]:
        """Get the full conversation log."""
        return self.conversation_log
    
    def print_conversation(self):
        """Pretty print the conversation."""
        for entry in self.conversation_log:
            print(f"\n[{entry['agent']}]: {entry['message']}")
    
    def reset_all_agents(self):
        """Clear conversation history for all agents."""
        for agent in self.agents.values():
            agent.clear_history()
        self.conversation_log = []


def ask_ai(prompt: str, act_as: str = "A helpful and accurate assistant.") -> str:
    """
    Public entrypoint for Opalib AI - single agent query.
    Requires absolutely NO API keys or configuration files.
    
    Args:
        prompt (str): The main request or question for the AI.
        act_as (str): The system persona/instructions dictating the AI's behavior.
    
    Returns:
        str: The AI's response.
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string.")

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
            return f"Opalib AI Error: Server returned status code {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "Opalib AI Error: The connection timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Opalib AI Error: Network problem encountered. Details: {e}"


def create_agent(name: str, system_prompt: str) -> Agent:
    """
    Create a new AI agent.
    
    Args:
        name (str): The agent's name.
        system_prompt (str): The system instructions defining the agent's personality and behavior.
    
    Returns:
        Agent: A new Agent object.
    """
    return Agent(name=name, system_prompt=system_prompt)
