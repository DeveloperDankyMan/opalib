import os
from genkit import Genkit
from genkit.plugins.google_genai import GoogleAI

# Initialize Genkit with the Google AI plugin
ai = Genkit(
    plugins=[GoogleAI()],
    model='googleai/gemini-2.5-flash',
)

# Define the Genkit Flow accepting both the prompt and the persona behavior
@ai.flow()
async def _internal_ai_flow(input_data: dict) -> str:
    """
    Executes the prompt orchestration with Genkit, feeding the system persona.
    """
    user_prompt = input_data.get("prompt")
    system_behavior = input_data.get("system_behavior")

    response = await ai.generate(
        system=system_behavior,  # <-- This tells Gemini exactly how to act!
        prompt=user_prompt,
    )
    return response.text

# Public user-facing function
def ask_ai(prompt: str, act_as: str = "A helpful and accurate assistant.") -> str:
    """
    Public entrypoint allowing users to define a custom persona behavior.
    
    Args:
        prompt (str): The question or message for the AI.
        act_as (str): The system prompt/persona instructing how the AI should act.
    """
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError(
            "Missing environment variable: 'GEMINI_API_KEY'. "
            "Please obtain a free key at Google AI Studio."
        )
        
    if not prompt or not isinstance(prompt, str):
        raise ValueError("Prompt must be a non-empty string.")

    # Package arguments into a dict for the flow
    payload = {
        "prompt": prompt,
        "system_behavior": act_as
    }

    try:
        result = ai.run_main(lambda: _internal_ai_flow(payload))
        return result
    except Exception as e:
        return f"Opalib AI Error: Could not generate response. Details: {e}"
