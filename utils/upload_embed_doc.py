import time
from typing import List, Dict, Optional, Tuple
# Import Pinecone client library - ensure it's in requirements.txt
from pinecone import Pinecone, ServerlessSpec, PodSpec
from services import pinecone_manager
from services import embedder
from services import file_processor

def upload_and_embed_document(
    user_namespace: str,
    file_path: str,
    actual_filename: str, 
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
) -> Optional[str]:
    """
    Processes a single document, generates embeddings, and upserts to Pinecone.

    Args:
        user_namespace: The namespace specific to the user.
        file_path: The path to the document file to process.
        chunk_size: Custom chunk size for this document.
        chunk_overlap: Custom chunk overlap for this document.

    Returns:
        The unique document ID if successful, otherwise None.
    """
    print(f"\n--- Starting Upload and Embedding for User: {user_namespace}, File: {file_path} ---")
    if not pinecone_manager.index or not embedder.client:
        print("Error: Services not initialized properly.")
        return None

    # 1. Process the file (load and chunk)
    processed_data = file_processor.process_file(file_path,actual_filename, chunk_size, chunk_overlap)
    if not processed_data:
        print(f"Failed to process file: {file_path}")
        return None

    document_id = processed_data["document_id"]
    chunks = processed_data["chunks"]
    original_filename = processed_data["original_filename"]

    # 2. Generate embeddings
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = embedder.get_embeddings(chunks)
    if not embeddings or len(embeddings) != len(chunks):
        print(f"Failed to generate embeddings for document: {document_id}")
        return None

    # 3. Upsert to Pinecone
    print(f"Upserting vectors to Pinecone namespace: {user_namespace}")
    try:
        pinecone_manager.upsert_vectors(
            user_namespace=user_namespace,
            document_id=document_id,
            chunks=chunks,
            embeddings=embeddings,
            original_filename=original_filename
        )
        print(f"Successfully processed and upserted document: {original_filename} (ID: {document_id})")
        return document_id
    except Exception as e:
        print(f"Failed to upsert vectors for document {document_id}: {e}")
        # Consider cleanup logic here if needed (e.g., deleting partially upserted data)
        return None