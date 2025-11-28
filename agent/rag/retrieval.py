from rank_bm25 import BM25Okapi
from .doc_loader import load_and_chunk_all

class Retriever:
    def __init__(self):
        self.chunks = load_and_chunk_all()
        self.corpus = [c["text"].split() for c in self.chunks]
        self.bm25 = BM25Okapi(self.corpus)

    def search(self, query, k=3):
        tokens = query.split()
        scores = self.bm25.get_scores(tokens)

        scored = list(zip(self.chunks, scores))
        ranked = sorted(scored, key=lambda x: x[1], reverse=True)

        results = []
        for chunk, score in ranked[:k]:
            results.append({
                "id": chunk["id"],
                "text": chunk["text"],
                "source": chunk["filename"],
                "score": float(score)
            })
        return results
