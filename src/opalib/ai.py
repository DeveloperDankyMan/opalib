import random
import requests

def ask_ai(prompt: str, act_as: str = "A helpful and accurate assistant.") -> str:
    """
    Public entrypoint for Opalib AI.
    Requires absolutely NO API keys or configuration files.
    
    Args:
        prompt (str): The main request or question for the AI.
        act_as (str): The system persona/instructions dictating the AI's behavior.
    """
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string.")

    url = "https://text.pollinations.ai"
    
    # Structure the message payload including your system prompt behavior
    payload = {
        "messages": [
            {"role": "system", "content": act_as},
            {"role": "user", "content": prompt}
        ],
        "model": "openai",                    # Default high-quality fallback text model
        "seed": random.randint(1, 99999999),  # Keeps results fresh and dynamic
        "jsonMode": False,
        "private": True
    }

    try:
        # Send a direct POST request to the public endpoint
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"Opalib AI Error: Server returned status code {response.status_code}"
            
    except requests.exceptions.Timeout:
        return "Opalib AI Error: The connection timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Opalib AI Error: Network problem encountered. Details: {e}"
