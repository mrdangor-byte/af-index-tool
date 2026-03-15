import numpy as np
import pandas as pd
from .types import IndexConfig, CutoffDirection


def build_deprivation_matrix(data: pd.DataFrame, config: IndexConfig) -> np.ndarray:
    """Build g0 matrix: N x d binary matrix where 1 = deprived."""
    n = len(data)
    d = len(config.indicators)
    g0 = np.zeros((n, d), dtype=np.float64)

    for j, ind in enumerate(config.indicators):
        values = data[ind.source_column].values.astype(np.float64)
        if ind.cutoff_direction == CutoffDirection.BELOW:
            g0[:, j] = (values < ind.deprivation_cutoff).astype(np.float64)
        else:
            g0[:, j] = (values > ind.deprivation_cutoff).astype(np.float64)

    return g0


def compute_deprivation_scores(g0: np.ndarray, config: IndexConfig) -> np.ndarray:
    """Compute weighted deprivation score c_i = sum(w_j * g0_ij) for each person."""
    weights = np.array([ind.weight for ind in config.indicators])
    return g0 @ weights


def apply_poverty_cutoff(
    g0: np.ndarray, scores: np.ndarray, k: float
) -> tuple[np.ndarray, np.ndarray]:
    """Apply dual cutoff: zero out rows where score < k.
    Returns (censored_g0, censored_scores)."""
    identified = scores >= k
    censored_g0 = g0.copy()
    censored_g0[~identified] = 0
    censored_scores = scores.copy()
    censored_scores[~identified] = 0
    return censored_g0, censored_scores
