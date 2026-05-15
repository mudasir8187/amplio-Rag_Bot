import config as config
from fastapi import APIRouter, Form, HTTPException
from pydantic import BaseModel
from services.embedder import get_chat_completion
from typing import Dict, List, Optional
from utils.query_doc_func import search_documents

router = APIRouter()

NO_KB_CONTENT_MESSAGE = (
    "No answer could be grounded in your uploaded documents for this question. "
    "Confirm the knowledge base name matches the one used at upload, try different wording, "
    "or add documents that cover this topic."
)

RAG_STRICT_PREAMBLE = """
You are answering for a regulated, accuracy-critical workflow.

Rules (must follow all):
1. Use ONLY information explicitly supported by the Context below. Treat the Context as the only source of truth.
2. If the Context does not contain enough information to answer the question, do not guess and do not use outside knowledge. Reply with a single short paragraph stating that the provided documents do not contain sufficient information to answer the question, and suggest what might be missing (e.g. pricing section, contract terms) without inventing facts.
3. If you can answer, base every factual claim on the Context. If something is unclear in the Context, say it is unclear rather than inferring.
4. Keep the same formatting preferences as below for structure when you do answer from the Context.

**Instructions for Answer Format (when answering from Context):**
- Structure the answer into distinct paragraphs for each main point/item.
- Use **bold text** (e.g., **Heading**) for each heading/point label.
- Avoid markdown beyond bold, special characters (`---`, `#`, `*`), or numbered lists unless explicitly requested.
- Keep explanations concise but complete.
"""


class QueryResponseWithAnswer(BaseModel):
    status: str
    ai_answer: Optional[str] = None
    results: List[Dict]
    count: int
    message: Optional[str] = None


def _namespace_from_name(name: str) -> str:
    return "".join(name.strip().lower().split())


@router.post("/query_document", response_model=QueryResponseWithAnswer)
async def query_document(
    name: str = Form(..., min_length=1, max_length=100),
    query: str = Form(...),
):
    """
    Query documents in the knowledge base identified by `name` (same rules as create).
    Answers are derived only from retrieved content; there is no general-knowledge fallback.
    """
    user_namespace = _namespace_from_name(name)
    top_k = config.top_k
    openai_chat_model = config.OPENAI_CHAT_MODEL
    temperature = config.OPENAI_TEMPERATURE
    max_tokens = config.OPENAI_MAX_TOKENS

    ai_generated_answer: Optional[str] = None
    formatted_results: List[Dict] = []
    search_message: Optional[str] = None

    try:
        results = search_documents(
            user_namespace=user_namespace,
            query_text=query,
            document_ids=None,
            top_k=top_k,
        )

        context_texts: List[str] = []
        if results:
            for result in results:
                metadata = result.get("metadata", {})
                chunk_text = metadata.get("text", "")
                if chunk_text:
                    context_texts.append(chunk_text)

                formatted_results.append(
                    {
                        "score": result.get("score", 0.0),
                        "original_filename": metadata.get("original_filename"),
                        "text": chunk_text,
                    }
                )

        if not context_texts:
            ai_generated_answer = NO_KB_CONTENT_MESSAGE
            search_message = (
                "Retrieval did not return usable text from this knowledge base for your query."
            )
        else:
            context_string = "\n\n---\n\n".join(context_texts)
            rag_prompt = f"""{RAG_STRICT_PREAMBLE}

Context:
---
{context_string}
---

User Question: {query}

Answer (from Context only, per rules above):
"""

            try:
                ai_generated_answer = get_chat_completion(
                    prompt=rag_prompt,
                    model=openai_chat_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                search_message = "Answer generated strictly from retrieved document excerpts."
            except Exception as ai_error:
                ai_generated_answer = (
                    "The assistant could not complete a document-grounded summary. "
                    "Please review the source excerpts below or try again later."
                )
                search_message = f"Answer generation failed: {str(ai_error)}"

        return {
            "status": "success",
            "ai_answer": ai_generated_answer,
            "results": formatted_results,
            "count": len(formatted_results),
            "message": search_message,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during the query: {str(e)}",
        ) from e
