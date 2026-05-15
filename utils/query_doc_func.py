from typing import Dict, List, Optional

import config
from services import pinecone_manager


def search_documents(
    user_namespace: str,
    query_text: str,
    document_ids: Optional[List[str]] = None,
    top_k: int = config.top_k,
) -> List[Dict]:
    """Search document chunks in a Pinecone namespace (optionally filtered by document IDs)."""
    print(f"\n--- Starting Search for User: {user_namespace} ---")
    print(f"Query: {query_text}")
    print(f"Top K: {top_k}")

    if document_ids:
        print(f"Filtering by Document IDs: {document_ids}")
    else:
        print("Searching across all documents in namespace.")

    if not pinecone_manager.index:
        print("Error: Pinecone index not initialized properly.")
        return []

    try:
        results = pinecone_manager.query_vectors(
            user_namespace=user_namespace,
            query_text=query_text,
            document_ids=document_ids,
            top_k=top_k,
        )
        print(f"Search completed. Found {len(results)} results.")
        return results
    except Exception as e:
        print(f"Search failed: {e}")
        return []
