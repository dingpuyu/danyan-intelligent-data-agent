"""Runtime knobs for retrieval quality and cost control."""
import os


def _int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, default)))
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    try:
        return min(1.0, max(0.0, float(os.getenv(name, default))))
    except ValueError:
        return default


MAX_RECALL_KEYWORDS = _int("RETRIEVAL_MAX_KEYWORDS", 8)
RECALL_TOP_K = _int("RETRIEVAL_TOP_K", 10)
RECALL_SCORE_THRESHOLD = _float("RETRIEVAL_SCORE_THRESHOLD", 0.6)
ES_VALUE_SIZE = _int("RETRIEVAL_ES_SIZE", 10)
