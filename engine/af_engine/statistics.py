import numpy as np
from scipy import stats


def spearman_correlation(ranks1: np.ndarray, ranks2: np.ndarray) -> float:
    """Compute Spearman rank correlation coefficient."""
    corr, _ = stats.spearmanr(ranks1, ranks2)
    return float(corr)


def kendall_correlation(ranks1: np.ndarray, ranks2: np.ndarray) -> float:
    """Compute Kendall tau rank correlation coefficient."""
    corr, _ = stats.kendalltau(ranks1, ranks2)
    return float(corr)


def rank_subgroups(subgroup_results: list, metric: str = "M0") -> np.ndarray:
    """Rank subgroups by a given metric. Returns array of ranks."""
    values = np.array(
        [
            getattr(r, metric) if hasattr(r, metric) else r[metric]
            for r in subgroup_results
        ]
    )
    # Use scipy rankdata (1-based ranks, average ties)
    return stats.rankdata(-values)  # negative for descending (highest M0 = rank 1)


def compare_rankings(results_a: list, results_b: list, metric: str = "M0") -> dict:
    """Compare rankings between two sets of results."""
    ranks_a = rank_subgroups(results_a, metric)
    ranks_b = rank_subgroups(results_b, metric)

    return {
        "spearman": spearman_correlation(ranks_a, ranks_b),
        "kendall": kendall_correlation(ranks_a, ranks_b),
        "n_groups": len(ranks_a),
    }
