from typing import List
import os

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.enabled = os.getenv("ENABLE_EMBEDDINGS", "True").lower() == "true"
        if self.enabled:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-mpnet-base-v2')
            except ImportError:
                print("sentence-transformers not installed. Embeddings disabled.")
                self.enabled = False

    def generate_embedding(self, text: str) -> List[float]:
        """Generate 512-dim embedding for a test case"""
        if not self.enabled or not self.model:
            # Return dummy 512-dim vector for tests/mock
            return [0.0] * 512
            
        vector = self.model.encode(text)
        # SBERT mpnet outputs 768-dim, but instructions say 512-dim.
        # We will truncate to 512-dim.
        return vector.tolist()[:512]

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate 512-dim embeddings for a batch of test cases"""
        if not self.enabled or not self.model:
            return [[0.0] * 512 for _ in texts]
        vectors = self.model.encode(texts)
        return [v.tolist()[:512] for v in vectors]

embedding_service = EmbeddingService()
