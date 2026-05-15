import time
from typing import List, Dict, Optional, Tuple
# Import Pinecone client library - ensure it's in requirements.txt
from pinecone import Pinecone, ServerlessSpec, PodSpec
import config as config
from services import embedder

# Initialize Pinecone client
pc = None
index = None

def init_pinecone():
    """Initializes the Pinecone client and connects to the index. Creates one if it doesn't exist."""
    global pc, index
    try:
        api_key = config.PINECONE_API_KEY
        environment = config.PINECONE_ENVIRONMENT
        index_name = config.PINECONE_INDEX_NAME

        if not api_key or api_key == "YOUR_PINECONE_API_KEY" or \
           not environment or environment == "YOUR_PINECONE_ENVIRONMENT" or \
           not index_name:
            raise ValueError("Pinecone API key, environment, or index name not configured.")

        pc = Pinecone(api_key=api_key)
        print("Pinecone client initialized.")

        # ✅ List existing indexes
        indexes = pc.list_indexes()
        index_names = [idx["name"] for idx in indexes]
        print(f"Available indexes: {index_names}")

        # ✅ If index doesn't exist, create it
        if index_name not in index_names:
            print(f"Index '{index_name}' not found. Creating new one...")
            pc.create_index(
                name=index_name,
                dimension=config.EMBEDDING_DIMENSION,  # ✅ Change to match your embedding dimension
                metric=config.index_matric,  # or "dotproduct", "euclidean"
                spec=ServerlessSpec(
                    cloud=config.cloud,   # or "gcp"
                    region=config.region  # pick a region supported by Pinecone
                )
            )
            print(f"Index '{index_name}' created successfully.")

        # ✅ Connect to the index
        index = pc.Index(index_name)
        print(f"Connected to Pinecone index: '{index_name}'")

    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
        pc = None
        index = None
        raise

def upsert_vectors(user_namespace: str, document_id: str, chunks: List[str], embeddings: List[List[float]], original_filename: str):
    """Upserts document chunks and their embeddings into a specific namespace."""
    if not index:
        raise ConnectionError("Pinecone index not initialized. Call init_pinecone() first.")
    if len(chunks) != len(embeddings):
        raise ValueError("Number of chunks and embeddings must match.")

    vectors_to_upsert = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vector_id = f"{document_id}-chunk-{i}" # Unique ID for each chunk vector
        metadata = {
            config.DOCUMENT_ID_META_KEY: document_id,
            "text": chunk, # Store the original text chunk in metadata
            "original_filename": original_filename,
            "chunk_index": i
        }
        vectors_to_upsert.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })

    if not vectors_to_upsert:
        print("No vectors to upsert.")
        return

    # Upsert in batches if necessary (Pinecone recommends batches of 100 or less)
    batch_size = 100
    for i in range(0, len(vectors_to_upsert), batch_size):
        batch = vectors_to_upsert[i:i+batch_size]
        try:
            print(f"Upserting batch {i//batch_size + 1} ({len(batch)} vectors) to namespace '{user_namespace}'...")
            index.upsert(vectors=batch, namespace=user_namespace)
            print("Batch upsert successful.")
        except Exception as e:
            print(f"Error upserting batch to Pinecone: {e}")
            # Consider adding retry logic here


def query_vectors(user_namespace: str, query_text: str, document_ids: Optional[List[str]] = None, top_k: int = 5) -> List[Dict]:
    """Queries the Pinecone index within a namespace, optionally filtering by document IDs."""
    if not index:
        raise ConnectionError("Pinecone index not initialized. Call init_pinecone() first.")

    try:
        # Get embedding for the query text
        query_embedding = embedder.get_embeddings([query_text])
        if not query_embedding:
            print("Failed to generate embedding for the query text.")
            return []

        # Construct the filter if document_ids are provided
        query_filter = None
        if document_ids:
            if len(document_ids) == 1:
                query_filter = {config.DOCUMENT_ID_META_KEY: document_ids[0]}
            else:
                query_filter = {config.DOCUMENT_ID_META_KEY: {"$in": document_ids}}
            print(f"Querying namespace '{user_namespace}' with filter: {query_filter}")
        else:
            print(f"Querying namespace '{user_namespace}' without document filter.")

        # Perform the query
        query_response = index.query(
            namespace=user_namespace,
            vector=query_embedding[0],
            top_k=top_k,
            include_metadata=True,
            filter=query_filter
        )

        # Format results
        results = []
        if query_response.matches:
            for match in query_response.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
        print(f"Query returned {len(results)} results.")
        return results

    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []



# Example Usage (for testing - requires Pinecone setup and OpenAI key)
if __name__ == '__main__':
    print("--- Testing Pinecone Manager ---")
    try:
        # Ensure config is loaded and OpenAI client is available
        config.validate_config()
        if not embedder.client:
             raise ValueError("OpenAI client not initialized in embedder.")

        # 1. Initialize Pinecone
        init_pinecone()

        # 2. Prepare dummy data for upsert
        test_user = "user-123"
        test_doc_id = "doc-abc"
        test_filename = "sample_test.txt"
        test_chunks = ["This is the first test chunk.", "This is the second test chunk."]
        test_embeddings = embedder.get_embeddings(test_chunks)

        if test_embeddings:
            # 3. Upsert data
            print(f"\n--- Testing Upsert --- ({test_user})")
            upsert_vectors(test_user, test_doc_id, test_chunks, test_embeddings, test_filename)
            print("Upsert test potentially successful (check Pinecone console).")
            # Wait a bit for index to update
            print("Waiting 5 seconds for index to update...")
            time.sleep(5)

            # 4. Query data (within the specific document)
            print(f"\n--- Testing Query (Filtered) --- ({test_user})")
            query = "first chunk"
            filtered_results = query_vectors(test_user, query, document_ids=[test_doc_id], top_k=2)
            print("Filtered Query Results:")
            for res in filtered_results:
                print(f"  ID: {res['id']}, Score: {res['score']:.4f}, Text: {res['metadata'].get('text')}")

            # 5. Query data (across all docs for the user)
            print(f"\n--- Testing Query (Unfiltered) --- ({test_user})")
            unfiltered_results = query_vectors(test_user, query, top_k=2)
            print("Unfiltered Query Results:")
            for res in unfiltered_results:
                print(f"  ID: {res['id']}, Score: {res['score']:.4f}, Text: {res['metadata'].get('text')}")
        else:
            print("Skipping upsert/query tests because embedding generation failed.")

    except (ValueError, ConnectionError, ImportError) as e:
        print(f"Pinecone Manager test failed: {e}")
    except Exception as e:
         print(f"An unexpected error occurred during testing: {e}")

    print("--- Test Complete ---")

