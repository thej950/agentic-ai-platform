from __future__ import annotations

from app.schemas.retrieval_response import RetrievalResponse


class PromptBuilder:
    """Build a prompt for a local, context-grounded mock LLM answer."""

    def build(self, question: str, retrieval_response: RetrievalResponse) -> str:
        context_chunks = [
            str(result.chunk_text).strip()
            for result in retrieval_response.results
            if str(result.chunk_text).strip()
        ]
        context = "\n\n".join(context_chunks)

        return (
            "------------------------------------------------\n"
            "System:\n\n"
            "You are an enterprise AI assistant.\n\n"
            "Answer ONLY using the provided context.\n\n"
            "If the answer is not available in the context, reply exactly:\n\n"
            '"I couldn\'t find this information in the uploaded documents."\n\n'
            "Do not hallucinate.\n"
            "Do not use outside knowledge.\n\n"
            "Context:\n"
            f"{context}\n\n"
            "Question:\n"
            f"{question}\n\n"
            "Answer:\n"
            "------------------------------------------------"
        )
