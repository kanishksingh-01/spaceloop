"""
SpaceLoop Content Similarity & Plagiarism Detector
Detects duplicate or cloned listings and copy-pasted review rings using:
1. Token n-gram Jaccard similarity (fast lexical filter)
2. Normalized dense vector embedding cosine similarity (deep semantic equivalence)
"""
import re
from backend.modules.search.embedding import generate_embedding, cosine_similarity


def tokenize_text(text: str) -> set[str]:
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 2]
    return set(tokens)


def compute_jaccard_similarity(text_a: str, text_b: str) -> float:
    tokens_a = tokenize_text(text_a)
    tokens_b = tokenize_text(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / float(len(union)) if union else 0.0


def compute_semantic_content_similarity(text_a: str, text_b: str) -> float:
    """
    Computes hybrid text similarity combining Jaccard lexical and vector cosine similarity.
    """
    if not text_a or not text_b:
        return 0.0

    # 1. Fast path: check identical or almost identical strings
    if text_a.strip().lower() == text_b.strip().lower():
        return 1.0

    jaccard = compute_jaccard_similarity(text_a, text_b)
    if jaccard > 0.85:
        return round(jaccard, 3)

    # 2. Vector semantic embedding comparison
    try:
        vec_a = generate_embedding(text_a)
        vec_b = generate_embedding(text_b)
        cos_sim = cosine_similarity(vec_a, vec_b)
        combined = (0.4 * jaccard) + (0.6 * cos_sim)
        return round(combined, 3)
    except Exception:
        return round(jaccard, 3)


def check_listing_duplication(candidate_space, existing_spaces: list, threshold: float = 0.85) -> dict:
    """
    Compares candidate space title & description against active marketplace listings.
    """
    c_desc = f"{candidate_space.title} {candidate_space.description or ''}"
    c_raw_desc = (candidate_space.description or "").strip()
    c_id = getattr(candidate_space, "id", None)
    c_owner = getattr(candidate_space, "owner_id", None)

    highest_sim = 0.0
    matched_space = None

    for sp in existing_spaces:
        sp_id = getattr(sp, "id", None)
        if c_id and sp_id == c_id:
            continue
        # Also compare across spaces
        sp_desc = f"{sp.title} {sp.description or ''}"
        sim_full = compute_semantic_content_similarity(c_desc, sp_desc)

        sp_raw_desc = (sp.description or "").strip()
        sim_desc = 0.0
        if len(c_raw_desc) > 20 and len(sp_raw_desc) > 20:
            sim_desc = compute_semantic_content_similarity(c_raw_desc, sp_raw_desc)

        sim = max(sim_full, sim_desc)
        if sim > highest_sim:
            highest_sim = sim
            matched_space = sp

    is_duplicate = highest_sim >= threshold
    return {
        "is_duplicate": is_duplicate,
        "similarity_score": highest_sim,
        "matched_space_id": getattr(matched_space, "id", None) if is_duplicate else None,
        "matched_space_title": getattr(matched_space, "title", None) if is_duplicate else None,
        "matched_space_owner_id": getattr(matched_space, "owner_id", None) if is_duplicate else None,
        "same_owner": bool(is_duplicate and c_owner and getattr(matched_space, "owner_id", None) == c_owner)
    }
