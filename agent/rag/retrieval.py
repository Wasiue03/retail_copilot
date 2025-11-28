import os
import glob
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Retriever:
    def __init__(self, docs_dir="docs", top_k=3):
        self.top_k = top_k
        self.chunks = []
        self.doc_texts = []
        self.ids = []

        self._load_docs(docs_dir)
        self.vectorizer = TfidfVectorizer().fit(self.doc_texts)
        self.doc_vectors = self.vectorizer.transform(self.doc_texts)

    def _load_docs(self, docs_dir):
        for filepath in glob.glob(os.path.join(docs_dir, "*.md")):
            with open(filepath, "r", encoding="utf-8") as f:
                paragraphs = [p.strip() for p in f.read().split("\n\n") if p.strip()]
                for idx, para in enumerate(paragraphs):
                    chunk_id = f"{os.path.basename(filepath)}::chunk{idx}"
                    self.ids.append(chunk_id)
                    self.doc_texts.append(para)
                    self.chunks.append({"id": chunk_id, "content": para, "source": filepath})

    def search(self, query):
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.doc_vectors)[0]
        top_idx = sims.argsort()[::-1][:self.top_k]
        results = []
        for i in top_idx:
            results.append({
                "id": self.ids[i],
                "content": self.doc_texts[i],
                "score": float(sims[i])
            })
        return results
