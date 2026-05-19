"""
LLMClient: constructs a grounded prompt and calls the Groq API.
Uses streaming internally and collects the full response.
"""
import logging
import re
from typing import List

from groq import Groq

from models import Citation, LLMResponse, RetrievedChunk

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """\
You are a helpful UMass HR assistant. Answer the question using ONLY the provided context.
If the context does not contain enough information, say so clearly.
Do NOT include any source references, filenames, or citations in your answer.

Context:
{context}

Question: {query}

Answer:"""


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, model: str, api_key: str):
        self._model = model
        self._client = Groq(api_key=api_key)

    def generate(self, query: str, context_chunks: List[RetrievedChunk]) -> LLMResponse:
        """
        Build prompt, call Groq API with streaming, return LLMResponse.
        Raises LLMError on API failure.
        """
        prompt = self._build_prompt(query, context_chunks)
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_completion_tokens=1024,
                top_p=0.95,
                stream=True,
                stop=None,
            )
            # Collect streamed chunks into a single answer string
            answer = "".join(
                chunk.choices[0].delta.content or ""
                for chunk in completion
            )
            answer = re.sub(r"<think>.*?</think>\s*", "", answer, flags=re.DOTALL).strip()
        except Exception as e:
            logger.error("Groq API error: %s", e)
            raise LLMError(f"Groq API call failed: {e}") from e

        citations = []
        seen = set()
        for chunk in context_chunks:
            source = chunk.metadata.source_url or chunk.metadata.source_filename or "unknown"
            title = chunk.metadata.document_title or source
            if source not in seen:
                citations.append(Citation(source=source, title=title))
                seen.add(source)

        return LLMResponse(answer=answer, citations=citations)

    def _build_prompt(self, query: str, chunks: List[RetrievedChunk]) -> str:
        context = "\n\n".join(chunk.text for chunk in chunks)
        return PROMPT_TEMPLATE.format(context=context, query=query)
