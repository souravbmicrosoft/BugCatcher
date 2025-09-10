from typing import List, Dict
from .indexer import search_index


def retrieve_for_frame(index_path: str, frame_raw: str, top_k: int = 5) -> List[Dict]:
    """Retrieve relevant code snippets for a given stack frame raw text."""
    return search_index(index_path, frame_raw, top_k=top_k)
