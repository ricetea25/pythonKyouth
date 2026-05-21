# prompt_mode.py

"""
Module for handling prompt modes for week2 project.
Add your code here.
"""

import os
from google import genai
from google.genai.errors import APIError

def prompt_model(model: str, prompt: str) -> str:
    """
    Prompts the specified Google AI model with an input string 
    and returns its text response safely.
    """
    # 1. Gracefully check for the environment token to prevent crashing
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Initialization Error: Please set the GEMINI_API_KEY environment variable."

    # 2. Map input shorthand aliases to ensure the function 'smartly selects' 
    # the correct identifier string expected by the Google backend endpoint.
    model_mapping = {
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
        "gemini-3-flash-preview": "gemini-3-flash-preview"
    }

    target_model = model_mapping.get(model.strip().lower())
    if not target_model:
        return f"Selection Error: Model string '{model}' is invalid or not supported."

    # 3. Execute generation wrapped inside protective blocks to capture unexpected errors
    try:
        # Client automatically discovers and reads GEMINI_API_KEY from environment
        client = genai.Client()
        response = client.models.generate_content(
            model=target_model,
            contents=prompt
        )
        
        # Guard against empty structures or missing blocks
        if response and response.text:
            return response.text
        return "Model Execution Note: The model completed successfully but returned an empty text body."

    except APIError as e:
        # Catches explicit Google network quota, structural limits, or credential denials
        return f"Google API Error encountered: {e.message} (Status Code: {e.code})"
    except Exception as e:
        # Broad catching barrier to keep the execution completely crash-proof
        return f"An unexpected execution anomaly occurred: {str(e)}"


def main():
    """Main verification hook block to test your prompt utility integration."""
    print("=== Testing prompt_model() Handler ===")
    
    # Simple evaluation payload criteria
    test_prompt = "What are the core differences between an API rate limit and a concurrent request throttle? Explain in 1 sentence."
    
    # Test cases mapping cross-model IDs
    test_models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3-flash-preview"
    ]
    
    for current_model in test_models:
        print(f"\n🚀 Sending prompt targeting: '{current_model}'...")
        result = prompt_model(model=current_model, prompt=test_prompt)
        print(f"📄 Response Content:\n{result}")
        print("-" * 50)

if __name__ == "__main__":
    main()