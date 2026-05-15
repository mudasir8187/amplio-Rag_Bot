from fastapi import APIRouter, File, UploadFile, Form, HTTPException
import os
import tempfile
import shutil

import config as config
from utils.upload_embed_doc import upload_and_embed_document

router = APIRouter()


def _namespace_from_name(name: str) -> str:
    return "".join(name.strip().lower().split())


@router.post("/create_knowledge_base")
async def create_knowledge_base(
    name: str = Form(..., min_length=1, max_length=100),
    file: UploadFile = File(..., description="Document to add to this knowledge base."),
):
    """
    Create or extend a knowledge base identified only by `name`.
    Chunk size and overlap use project defaults from config.
    """
    kb_namespace = _namespace_from_name(name)
    chunk_size = config.DEFAULT_CHUNK_SIZE
    chunk_overlap = config.DEFAULT_CHUNK_OVERLAP

    temp_file_path = None
    kb_file_name = file.filename or "upload"

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(kb_file_name)[1]
        ) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        document_id = upload_and_embed_document(
            user_namespace=kb_namespace,
            file_path=temp_file_path,
            actual_filename=kb_file_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        if not document_id:
            raise HTTPException(
                status_code=500,
                detail="Processing failed; check server logs.",
            )

        return {
            "name": name.strip(),
            "namespace": kb_namespace,
            "file_name": kb_file_name,
            "status": "success",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
        if hasattr(file, "file") and hasattr(file.file, "close") and not file.file.closed:
            file.file.close()
