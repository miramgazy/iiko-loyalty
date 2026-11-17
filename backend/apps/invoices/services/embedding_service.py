import logging
import os
from typing import List, Optional, Dict, Any
import httpx

from apps.core.models import Organization

logger = logging.getLogger(__name__)

GEMINI_EMBEDDING_MODEL = "text-embedding-004"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 768


class EmbeddingService:
    def __init__(self, organization: Organization):
        self.org = organization
        self.provider = (organization.vision_llm_provider or "gemini").lower()
        self.api_key = (
            organization.vision_llm_api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or ""
        )
        self.base_url = (organization.vision_llm_base_url or "").rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def get_embedding(self, text: str) -> Optional[List[float]]:
        if not text or not self.is_configured():
            return None
        res = self.get_embeddings_batch([text])
        return res[0] if res else None

    def get_embeddings_batch(
        self, texts: List[str], batch_size: int = 50
    ) -> List[Optional[List[float]]]:
        if not texts or not self.is_configured():
            return [None] * len(texts)

        results: List[Optional[List[float]]] = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            try:
                if self.provider == "openai":
                    chunk_embeddings = self._embed_openai_batch(chunk)
                else:
                    # По умолчанию Gemini
                    chunk_embeddings = self._embed_gemini_batch(chunk)
                results.extend(chunk_embeddings)
            except Exception as e:
                logger.error(f"Error computing embeddings batch ({len(chunk)} texts): {e}")
                results.extend([None] * len(chunk))

        return results

    def _embed_gemini_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        url = (
            f"{self.base_url}/v1beta/models/{GEMINI_EMBEDDING_MODEL}:batchEmbedContents?key={self.api_key}"
            if self.base_url
            else f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_EMBEDDING_MODEL}:batchEmbedContents?key={self.api_key}"
        )

        requests_payload = [
            {
                "model": f"models/{GEMINI_EMBEDDING_MODEL}",
                "content": {"parts": [{"text": t[:1000]}]},  # ограничение длины
            }
            for t in texts
        ]

        payload = {"requests": requests_payload}
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        embeddings_data = data.get("embeddings", [])
        output: List[Optional[List[float]]] = []
        for item in embeddings_data:
            vals = item.get("values")
            if vals and len(vals) == EMBEDDING_DIMENSIONS:
                output.append(vals)
            elif vals:
                # В случае нестандартной размерности
                output.append(vals[:EMBEDDING_DIMENSIONS])
            else:
                output.append(None)

        # Выравниваем длину
        while len(output) < len(texts):
            output.append(None)
        return output

    def _embed_openai_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        url = (
            f"{self.base_url}/v1/embeddings"
            if self.base_url
            else "https://api.openai.com/v1/embeddings"
        )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": OPENAI_EMBEDDING_MODEL,
            "dimensions": EMBEDDING_DIMENSIONS,
            "input": [t[:1000] for t in texts],
        }

        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        items = data.get("data", [])
        # Сортируем по индексу для сохранения порядка
        items.sort(key=lambda x: x.get("index", 0))
        output = [item.get("embedding") for item in items]

        while len(output) < len(texts):
            output.append(None)
        return output
