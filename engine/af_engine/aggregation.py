import numpy as np
from .types import HeadlineResults


def compute_headcounts(censored_scores: np.ndarray, k: float) -> tuple[int, int]:
    """Return (q, n) where q = number identified."""
    n = len(censored_scores)
    q = int(np.sum(censored_scores >= k))
    return q, n


def compute_H(q: int, n: int) -> float:
    """Headcount ratio."""
    if n == 0:
        return 0.0
    return q / n


def compute_A(censored_scores: np.ndarray, k: float) -> float:
    """Average intensity among identified."""
    identified = censored_scores[censored_scores >= k]
    if len(identified) == 0:
        return 0.0
    return float(np.mean(identified))


def compute_M0(censored_scores: np.ndarray) -> float:
    """M0 = mean of all censored scores (equivalent to H*A)."""
    if len(censored_scores) == 0:
        return 0.0
    return float(np.mean(censored_scores))


def aggregate(censored_scores: np.ndarray, k: float) -> HeadlineResults:
    """Compute all headline results."""
    q, n = compute_headcounts(censored_scores, k)
    H = compute_H(q, n)
    A = compute_A(censored_scores, k)
    M0 = compute_M0(censored_scores)
    return HeadlineResults(H=H, A=A, M0=M0, q=q, n=n)
