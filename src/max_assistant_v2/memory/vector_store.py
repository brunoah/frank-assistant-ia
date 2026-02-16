# src/max_assistant_v2/memory/vector_store.py
import os, json
import faiss
import numpy as np

class VectorStore:
    def __init__(self, dir_path: str, embeddings):
        self.dir = dir_path
        self.embeddings = embeddings
        os.makedirs(self.dir, exist_ok=True)

        self.index_path = os.path.join(self.dir, "index.faiss")
        self.meta_path = os.path.join(self.dir, "meta.jsonl")

        self._items = []  # [{"text":..., "metadata": {...}}]

        self._load_meta()
        self._load_or_create_index()

    def _load_meta(self):
        if not os.path.exists(self.meta_path):
            open(self.meta_path, "a", encoding="utf-8").close()
        with open(self.meta_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    j = json.loads(line)
                    self._items.append({
                        "text": j.get("text", ""),
                        "metadata": j.get("metadata", {}) or {},
                    })


    def _load_or_create_index(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            return

        # dimension du modèle
        probe = self.embeddings.encode(["test"])
        dim = int(probe.shape[1])
        self.index = faiss.IndexFlatIP(dim)  # cosine via normalize_embeddings=True
        faiss.write_index(self.index, self.index_path)

        # si on a du meta sans index (rare), on reconstruit
        if self._items:
            texts = [it["text"] for it in self._items]
            vecs = self.embeddings.encode(texts).astype("float32")

            self.index.add(vecs)
            faiss.write_index(self.index, self.index_path)

    def add(self, text: str, metadata: dict | None = None):
        vec = self.embeddings.encode([text]).astype("float32")
        self.index.add(vec)
        faiss.write_index(self.index, self.index_path)

        rec = {"text": text, "metadata": metadata or {}}
        with open(self.meta_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._items.append(rec)

    def search(self, query: str, k: int = 4, min_score: float = 0.0) -> list[dict]:
        if self.index.ntotal == 0:
            return []

        qv = self.embeddings.encode([query]).astype("float32")
        scores, ids = self.index.search(qv, k)

        out = []
        for score, idx in zip(scores[0], ids[0]):
            if idx < 0:
                continue
            if 0 <= idx < len(self._items):
                s = float(score)
                if s >= float(min_score):
                    it = self._items[idx]
                    out.append({
                        "text": it.get("text", ""),
                        "metadata": it.get("metadata", {}) or {},
                        "score": s,
                    })
        return out

