import numpy as np
from .types import IndexConfig, DimensionalBreakdown, SubgroupResult, HeadlineResults
from .aggregation import aggregate


def dimensional_breakdown(
    g0: np.ndarray,
    censored_g0: np.ndarray,
    config: IndexConfig,
    M0: float,
) -> list[DimensionalBreakdown]:
    """Compute censored headcount ratios and percentage contributions."""
    results = []
    n = g0.shape[0]

    for j, ind in enumerate(config.indicators):
        raw_hc = float(np.mean(g0[:, j]))
        censored_hc = float(np.mean(censored_g0[:, j]))
        abs_contrib = ind.weight * censored_hc
        pct_contrib = (abs_contrib / M0 * 100) if M0 > 0 else 0.0

        results.append(
            DimensionalBreakdown(
                indicator_name=ind.name,
                dimension=ind.dimension,
                weight=ind.weight,
                censored_headcount=censored_hc,
                raw_headcount=raw_hc,
                contribution=pct_contrib,
                absolute_contribution=abs_contrib,
            )
        )

    return results


def subgroup_decomposition(
    censored_scores: np.ndarray,
    subgroup_values: np.ndarray,
    k: float,
    overall_M0: float,
) -> list[SubgroupResult]:
    """Decompose M0 by subgroup."""
    unique_groups = np.unique(subgroup_values)
    N = len(censored_scores)
    results = []

    for group in unique_groups:
        mask = subgroup_values == group
        group_scores = censored_scores[mask]
        group_result = aggregate(group_scores, k)

        n_l = int(np.sum(mask))
        v_l = n_l / N
        poverty_share = (
            (v_l * group_result.M0 / overall_M0 * 100) if overall_M0 > 0 else 0.0
        )

        results.append(
            SubgroupResult(
                group_value=str(group),
                n=n_l,
                q=group_result.q,
                H=group_result.H,
                A=group_result.A,
                M0=group_result.M0,
                population_share=v_l,
                poverty_share=poverty_share,
                delta=group_result.M0 - overall_M0,
            )
        )

    return sorted(results, key=lambda x: x.M0, reverse=True)
