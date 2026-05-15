import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# --- Pinecone Configuration ---
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
print("Pinecone API Key: ", PINECONE_API_KEY)
print("OpenAI API Key: ", OPENAI_API_KEY)
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
# Define a name for your Pinecone index
# Ensure this index is created in your Pinecone account with the correct dimension
PINECONE_INDEX_NAME = "boxology" # Replace with your desired index name

# --- OpenAI Configuration ---
# Specify the OpenAI embedding model to use
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
# For text-embedding-ada-002, the dimension is 1536
EMBEDDING_DIMENSION = 3072
index_matric = "cosine"
cloud = "aws"
region = "us-east-1"
# List of available OpenAI chat models
AVAILABLE_OPENAI_CHAT_MODELS = [
"gpt-4o","gpt-4o-mini", "gpt-5", "gpt-5-mini"
]

# Default OpenAI chat model to use
OPENAI_CHAT_MODEL = AVAILABLE_OPENAI_CHAT_MODELS[1] # Defaults to the first model in the list

OPENAI_MAX_TOKENS = 2000
OPENAI_TEMPERATURE = 0.9
print(OPENAI_TEMPERATURE)

# Fallback and Evaluation Model Parameters
OPENAI_FALLBACK_MAX_TOKENS = 50  # Max tokens for the general knowledge fallback answer
OPENAI_EVALUATION_MAX_TOKENS = 20 # Max tokens for the evaluation LLM's response
OPENAI_EVALUATION_TEMPERATURE = 0.0 # Temperature for the evaluation LLM (0.0 for deterministic output)

# --- File Processing Configuration ---
# Default chunk size and overlap, can be overridden during processing
DEFAULT_CHUNK_SIZE = 1000 # Number of characters per chunk
DEFAULT_CHUNK_OVERLAP = 200 # Number of characters to overlap between chunks

# --- Metadata Configuration ---
# Define the key used in Pinecone metadata to store the unique document ID
DOCUMENT_ID_META_KEY = "document_id"

top_k = 10



# --- Dynamic Config Updater ---
def update_chunk_config(chunk_size: int, chunk_overlap: int):
    """
    Updates the global config values for chunking dynamically.
    """
    global DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
    DEFAULT_CHUNK_SIZE = chunk_size
    DEFAULT_CHUNK_OVERLAP = chunk_overlap
    print(f"Chunk config updated: Size={DEFAULT_CHUNK_SIZE}, Overlap={DEFAULT_CHUNK_OVERLAP}")

# --- Validation ---
def validate_config():
    """
    Checks if essential configuration variables are set.
    """
    errors = []
    if not PINECONE_API_KEY or PINECONE_API_KEY == "YOUR_PINECONE_API_KEY":
        errors.append("PINECONE_API_KEY is not set in the .env file.")
    if not PINECONE_ENVIRONMENT or PINECONE_ENVIRONMENT == "YOUR_PINECONE_ENVIRONMENT":
        errors.append("PINECONE_ENVIRONMENT is not set in the .env file.")
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        errors.append("OPENAI_API_KEY is not set in the .env file.")
    if not PINECONE_INDEX_NAME:
        errors.append("PINECONE_INDEX_NAME is not defined in config.py.")

    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))

print("Configuration loaded.")
