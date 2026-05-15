import config
from services import pinecone_manager
from services import embedder

def initialize_services():
    """Initializes necessary services like Pinecone."""
    print("Initializing services...")
    try:
        config.validate_config() # Validate essential configs first
        pinecone_manager.init_pinecone()
        # Add other initializations if needed (e.g., embedding model loading)
        if not embedder.client:
             print("Warning: OpenAI client not initialized. Embedding/Querying will fail.")
             # Depending on requirements, might want to raise an error here
        print("Services initialized successfully.")
        return True
    except (ValueError, ConnectionError, ImportError) as e:
        print(f"Initialization failed: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during initialization: {e}")
        return False