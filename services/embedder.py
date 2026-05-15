# services/embedder.py

from typing import List
import time

# Import OpenAI library - ensure it's in requirements.txt
from openai import OpenAI

import config as config

# Initialize OpenAI client
# Ensure OPENAI_API_KEY is set in the environment or .env file
if config.OPENAI_API_KEY and config.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY":
    client = OpenAI(api_key=config.OPENAI_API_KEY)
else:
    client = None
    print("Warning: OPENAI_API_KEY not found. Embedding and Chat Completion will fail.")

def get_embeddings(texts: List[str], model: str = config.OPENAI_EMBEDDING_MODEL) -> List[List[float]]:
    """Generates embeddings for a list of texts using the specified OpenAI model."""
    if not client:
        raise ValueError("OpenAI client is not initialized. Check API key.")
    if not texts:
        return []

    embeddings = []
    try:
        # OpenAI API might have rate limits, handle potential errors
        # Consider adding batching and retry logic for production use
        response = client.embeddings.create(input=texts, model=model)
        embeddings = [item.embedding for item in response.data]
        print(f"Successfully generated {len(embeddings)} embeddings using model {model}.")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Depending on the error, you might want to retry or handle differently
        # For simplicity, we'll return empty list on error here
        return []
        
    return embeddings

def get_chat_completion(
    prompt: str, 
    model: str = config.OPENAI_CHAT_MODEL, 
    # Add temperature and max_tokens as parameters with defaults from config
    temperature: float = config.OPENAI_TEMPERATURE, 
    max_tokens: int = config.OPENAI_MAX_TOKENS
) -> str:
    """Generates a chat completion response from OpenAI based on the provided prompt and parameters."""
    if not client:
        raise ValueError("OpenAI client is not initialized. Check API key.")
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    try:
        print(f"Sending prompt to OpenAI model: {model} (Temp: {temperature}, Max Tokens: {max_tokens})")
        # Using the chat completions endpoint
        response = client.chat.completions.create(
            model=model, # Use model from parameter
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            # temperature=temperature, # Use temperature from parameter
            **({"temperature": temperature} if "gpt-5" not in model.lower() else {}), # Conditionally pass temperature
            **({"max_completion_tokens": max_tokens} if "gpt-5" in model.lower() else {"max_tokens": max_tokens})
            # max_tokens=max_tokens # Use max_tokens from parameter
        )
        
        # Extract the response content
        if response.choices and response.choices[0].message:
            completion_text = response.choices[0].message.content.strip()
            print("Received chat completion from OpenAI.")
            return completion_text
        else:
            print("OpenAI response did not contain expected content.")
            return "Error: Could not generate a response from AI." # Or raise an error

    except Exception as e:
        print(f"Error calling OpenAI chat completion API: {e}")
        # Return a specific error message or raise the exception
        # import traceback; traceback.print_exc() # For detailed debugging
        return f"Error: Failed to get response from AI. Details: {str(e)}"

# Example Usage (for testing)
if __name__ == '__main__':
    print("--- Testing Embedder & Chat Completion ---")
    if not client:
        print("Skipping tests as OpenAI client is not initialized.")
    else:
        # --- Embedding Test ---
        print("\n--- Embedding Test ---")
        sample_texts = [
            "This is the first chunk of text.",
            "Here is another piece of content.",
            "And a final segment for embedding."
        ]
        try:
            embeddings_result = get_embeddings(sample_texts)
            if embeddings_result:
                print(f"Generated {len(embeddings_result)} embeddings.")
                print(f"Dimension of the first embedding: {len(embeddings_result[0])}")
            else:
                print("Embedding generation failed.")
        except ValueError as e:
            print(f"Embedding test failed: {e}")
            
        # --- Chat Completion Test (with dynamic params) ---
        print("\n--- Chat Completion Test ---")
        test_prompt = "Explain the concept of vector embeddings in simple terms."
        try:
            # Test with default params
            print("\nTesting with default parameters:")
            completion_result_default = get_chat_completion(test_prompt)
            print(f"Prompt: {test_prompt}")
            print(f"Default Completion: {completion_result_default}")
            
            # Test with specific params
            print("\nTesting with specific parameters (temp=0.2, max_tokens=50):")
            completion_result_specific = get_chat_completion(
                prompt=test_prompt, 
                temperature=0.2, 
                max_tokens=50
            )
            print(f"Prompt: {test_prompt}")
            print(f"Specific Completion: {completion_result_specific}")

        except ValueError as e:
            print(f"Chat completion test failed: {e}")
            
    print("\n--- Test Complete ---")



