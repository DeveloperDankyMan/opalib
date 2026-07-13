"""
opalib.ai - Access artificial intelligence for free using g4f (gpt4free).
No API keys required. Works with multiple free AI providers.

Installation: pip install g4f
"""

import time
from typing import Optional

try:
    from g4f.client import Client
except ImportError:
    raise ImportError("g4f is required. Install it with: pip install g4f")

class AIAgent:
    """An AI Agent powered by g4f supporting free AI access and function calling."""
    
    def __init__(self, name: str, role: str, target_model: str = "gpt-4"):
        self.name = name
        self.role = role
        self.target_model = target_model
        self.client = Client()
        self.chat_history = []
        
        # Enforce agent context
        self.chat_history.append({
            "role": "system", 
            "content": f"Your name is {self.name}. Your role: {self.role}. Stay in character."
        })

    def ask(self, message: str, tools: Optional[List[Dict[str, Any]]] = None, available_functions: Optional[Dict[str, Callable]] = None) -> str:
        """Send a message and get a response from the AI, handling function calls if provided."""
        self.chat_history.append({"role": "user", "content": message})
        
        try:
            # Step 1: Send initial request to the model with tool definitions
            kwargs = {
                "model": self.target_model,
                "messages": self.chat_history,
                "timeout": 30
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            message_obj = response.choices[0].message
            reply = message_obj.content
            tool_calls = getattr(message_obj, "tool_calls", None)

            # Step 2: Check if the model decided to call a function
            if tool_calls and available_functions:
                # Save the model's intent to call a function to the history
                self.chat_history.append(message_obj)
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    
                    if function_name in available_functions:
                        import json
                        # Parse arguments provided by the model
                        function_args = json.loads(tool_call.function.arguments)
                        
                        # Execute the local Python function
                        function_to_call = available_functions[function_name]
                        function_response = function_to_call(**function_args)
                        
                        # Feed the function result back to the model
                        self.chat_history.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": str(function_response),
                        })
                
                # Step 3: Get a final text response from the model based on the function result
                second_response = self.client.chat.completions.create(
                    model=self.target_model,
                    messages=self.chat_history,
                    timeout=30
                )
                reply = second_response.choices[0].message.content

        except Exception as e:
            reply = f"⚠️ Error: {str(e)}"
            
        # Update history with the final text reply
        self.chat_history.append({"role": "assistant", "content": reply})
        return reply

class AgentSession:
    """Orchestrates conversations between AI agents powered by g4f."""
    
    def __init__(self, session_name: str, model: str = "gpt-4"):
        self.session_name = session_name
        self.model = model
        self.agents = []
        print(f"✓ Session initialized: '{self.session_name}' using model: {self.model}")
    
    def add_agent(self, agent: AIAgent):
        """Register an agent for this session."""
        self.agents.append(agent)
        print(f"🔄 Registered Agent: [{agent.name}] Role: {agent.role}")
    
    def run_discussion(self, topic: str, rounds: int = 1):
        """Run a multi-round discussion between agents on a given topic."""
        print(f"\n🚀 Session '{self.session_name}' Active")
        print(f"Topic: {topic}")
        print(f"Rounds: {rounds}")
        print("=" * 60)
        
        current_context = f"The active topic is: {topic}. Give your professional assessment."
        
        for r in range(1, rounds + 1):
            print(f"\n--- Round {r} ---")
            for agent in self.agents:
                print(f"📡 {agent.name} is thinking...")
                response = agent.ask(current_context)
                
                print(f"\033[96m[{agent.name}]\033[0m: {response}\n")
                
                current_context = f"{agent.name} stated: '{response}'. Address this statement directly."
                time.sleep(1)  # Rate limiting to be respectful
        
        print("=" * 60)
        print("✓ Discussion complete!")


# Optional: Alternative models available in g4f
AVAILABLE_MODELS = {
    "gpt-4": "OpenAI GPT-4",
    "gpt-4o": "OpenAI GPT-4 Optimized",
    "claude": "Anthropic Claude",
    "gemini": "Google Gemini",
    "llama": "Meta Llama",
    "mistral": "Mistral AI",
}


def list_available_models() -> dict:
    """Return available models in g4f."""
    return AVAILABLE_MODELS
