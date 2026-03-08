from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_embeddings(titles: list[str]) -> tuple[TfidfVectorizer | None, Any]:
    """Build TF-IDF embeddings with a safe fallback.

    Some small datasets may produce an empty vocabulary with strict `min_df`.
    Try `min_df=2` first, fall back to `min_df=1`, and finally return an
    empty sparse matrix if vectorization still fails.
    """
    try:
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=3000)
        mat = vec.fit_transform(titles)
        if mat.shape[1] == 0:
            raise ValueError("empty vocabulary")
        return vec, mat
    except Exception:
        try:
            vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=3000)
            mat = vec.fit_transform(titles)
            if mat.shape[1] == 0:
                raise ValueError("empty vocabulary")
            return vec, mat
        except Exception:
            # Return a placeholder empty matrix so callers can handle gracefully
            empty = csr_matrix((len(titles), 0))
            return None, empty


def similar_titles(df: pd.DataFrame, mat: Any, video_id: str, top_k: int) -> list[dict]:
    """Return top-k similar titles; handles empty matrices and missing ids."""
    # Normalize both sides to string to avoid int/str mismatches from query params.
    idx = df.index[df["video_id"].astype(str) == str(video_id)]
    if len(idx) == 0:
        return []
    i = int(idx[0])
    # If mat is None or empty, return empty list
    if mat is None:
        return []
    if hasattr(mat, "shape") and mat.shape[0] == 0:
        return []

    # Protect against index errors if shapes don't match
    try:
        sims = cosine_similarity(mat[i], mat).flatten()
    except Exception:
        return []

    order = np.argsort(-sims)
    out: list[dict] = []
    for j in order[1 : top_k + 1]:
        # ensure j is valid index
        if j < 0 or j >= len(df):
            continue
        out.append(
            {
                "video_id": str(df.at[j, "video_id"]),
                "title": str(df.at[j, "title"]),
                "similarity": float(sims[j]),
                "views": int(df.at[j, "views"]),
                "engagement_rate": float(df.at[j, "engagement_rate"]),
            }
        )
    return out
