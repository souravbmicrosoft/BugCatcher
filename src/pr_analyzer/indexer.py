import os
import hashlib
import json
from typing import List, Dict, Optional

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

import faiss
import numpy as np
import openai


DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CHUNK = 1024


def _walk_files(repo_path: str) -> List[str]:
    files = []
    for root, dirs, filenames in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in (".git", "venv", "node_modules")]
        for f in filenames:
            if f.endswith((".py", ".js", ".ts", ".java", ".cs", ".go", ".cpp", ".c", ".rs")):
                files.append(os.path.join(root, f))
    return files


def _read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


def _chunk_code(code: str, chunk_size: int = DEFAULT_CHUNK) -> List[str]:
    if not code:
        return []
    chunks = [code[i : i + chunk_size] for i in range(0, len(code), chunk_size)]
    return chunks


def _meta_path(index_path: str) -> str:
    return index_path + ".meta"


def _emb_path(index_path: str) -> str:
    return index_path + ".npy"


class EmbeddingProvider:
    """Abstract embedding provider. Currently supports sentence-transformers and OpenAI."""

    def __init__(self, model_name: str = DEFAULT_MODEL, use_openai: bool = False):
        self.use_openai = use_openai
        self.model_name = model_name
        # test/dummy mode: use a lightweight deterministic embedding for unit tests
        self._test_mode = os.getenv("PR_ANALYZER_UNIT_TEST", "0") == "1"
        if self._test_mode:
            self.model = None
            self._dim = 8
            return

        if not use_openai and SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not available in environment")
        if not use_openai:
            self.model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        if self._test_mode:
            # deterministic small embeddings for tests: hash -> bytes -> floats
            arrs = []
            for t in texts:
                h = hashlib.sha256(t.encode()).digest()
                vals = np.frombuffer(h, dtype=np.uint8).astype(np.float32)[: self._dim]
                # normalize
                vals = vals / (vals.sum() + 1e-9)
                arrs.append(vals)
            return np.vstack(arrs)
        if self.use_openai:
            # batch via OpenAI
            embs = []
            for t in texts:
                resp = openai.Embedding.create(input=t, model=self.model_name)
                embs.append(np.array(resp["data"][0]["embedding"]))
            return np.vstack(embs)
        else:
            return self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)


def build_index(repo_path: str, index_path: str, chunk_size: int = DEFAULT_CHUNK, model_name: str = DEFAULT_MODEL, use_openai: bool = False):
    """Index the repo into a FAISS index at `index_path`. Supports incremental runs by skipping previously hashed chunks."""
    files = _walk_files(repo_path)
    provider = EmbeddingProvider(model_name=model_name, use_openai=use_openai)

    metas: List[Dict] = []
    existing_hashes = set()
    if os.path.exists(_meta_path(index_path)):
        try:
            metas = json.load(open(_meta_path(index_path), "r", encoding="utf-8"))
            existing_hashes = {m.get("hash") for m in metas if m.get("hash")}
        except Exception:
            metas = []

    texts = []
    new_metas = []
    for p in files:
        code = _read_file(p)
        if not code:
            continue
        chunks = _chunk_code(code, chunk_size)
        for i, chunk in enumerate(chunks):
            h = hashlib.sha1(chunk.encode()).hexdigest()
            if h in existing_hashes:
                continue
            texts.append(chunk)
            new_metas.append({"path": p, "chunk_index": i, "hash": h})

    if not texts and metas:
        print("No new chunks to index; existing index retained.")
        return

    # compute embeddings for new texts
    embeddings = provider.embed(texts)

    # load or create faiss index
    dim = embeddings.shape[1]
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
    else:
        index = faiss.IndexFlatL2(dim)

    index.add(embeddings)
    faiss.write_index(index, index_path)

    # append metas and save
    metas.extend(new_metas)
    with open(_meta_path(index_path), "w", encoding="utf-8") as fh:
        json.dump(metas, fh)

    # optionally save raw embeddings (for debugging)
    try:
        if os.path.exists(_emb_path(index_path)):
            old = np.load(_emb_path(index_path))
            combined = np.vstack([old, embeddings])
        else:
            combined = embeddings
        np.save(_emb_path(index_path), combined)
    except Exception:
        pass

    print(f"Indexed {len(new_metas)} new chunks from {len(files)} files to {index_path}")


def search_index(index_path: str, query: str, top_k: int = 5, model_name: str = DEFAULT_MODEL) -> List[Dict]:
    provider = EmbeddingProvider(model_name=model_name, use_openai=False)
    q_emb = provider.embed([query])
    index = faiss.read_index(index_path)
    D, I = index.search(q_emb, top_k)
    metas = json.load(open(_meta_path(index_path), "r", encoding="utf-8"))
    results = []
    for idx in I[0]:
        if idx < 0 or idx >= len(metas):
            continue
        m = metas[idx]
        try:
            code = _read_file(m["path"])
            chunks = _chunk_code(code, chunk_size=int(m.get("chunk_size", DEFAULT_CHUNK)))
            snippet = chunks[m["chunk_index"]] if m["chunk_index"] < len(chunks) else ""
        except Exception:
            snippet = ""
        results.append({**m, "snippet": snippet})
    return results
