import numpy as np
import pandas as pd
from copy import deepcopy
from .types import IndexConfig, RobustnessResult
from .identification import (
    build_deprivation_matrix,
    compute_deprivation_scores,
    apply_poverty_cutoff,
)
from .aggregation import aggregate


def k_robustness(data: pd.DataFrame, config: IndexConfig) -> list[dict]:
    """Compute H, A, M0 across all meaningful k values."""
    g0 = build_deprivation_matrix(data, config)
    scores = compute_deprivation_scores(g0, config)
    weights = np.array([ind.weight for ind in config.indicators])

    # Get all unique possible k values (each weight and cumulative sums)
    min_w = float(min(weights))
    d = len(weights)
    # Use exact fractions (i * min_w) to avoid floating-point drift from arange
    possible_k = sorted(set(i * min_w for i in range(1, d + 1)))
    # Also ensure we include the configured k
    if not any(np.isclose(config.poverty_cutoff_k, pk) for pk in possible_k):
        possible_k.append(config.poverty_cutoff_k)
        possible_k.sort()

    results = []
    for k_val in possible_k:
        if k_val <= 0 or k_val > 1:
            continue
        _, censored_scores = apply_poverty_cutoff(g0, scores, k_val)
        result = aggregate(censored_scores, k_val)
        results.append(
            {
                "k": round(float(k_val), 10),
                "H": result.H,
                "A": result.A,
                "M0": result.M0,
                "q": result.q,
            }
        )

    return results


def weight_robustness(
    data: pd.DataFrame, config: IndexConfig, n_scenarios: int = 100
) -> list[dict]:
    """Test robustness to different weight schemes using random Dirichlet weights."""
    rng = np.random.default_rng(42)
    g0 = build_deprivation_matrix(data, config)
    d = len(config.indicators)
    results = []

    for i in range(n_scenarios):
        # Generate random weights that sum to 1
        random_weights = rng.dirichlet(np.ones(d))

        # Create modified config
        scores = g0 @ random_weights
        _, censored_scores = apply_poverty_cutoff(g0, scores, config.poverty_cutoff_k)
        result = aggregate(censored_scores, config.poverty_cutoff_k)

        results.append(
            {
                "scenario": i,
                "weights": random_weights.tolist(),
                "H": result.H,
                "A": result.A,
                "M0": result.M0,
            }
        )

    return results


def leave_one_out(data: pd.DataFrame, config: IndexConfig) -> list[dict]:
    """Drop each indicator one at a time and recompute."""
    results = []

    for drop_idx, dropped in enumerate(config.indicators):
        remaining = [ind for i, ind in enumerate(config.indicators) if i != drop_idx]

        # Re-normalize weights to sum to 1
        total_w = sum(ind.weight for ind in remaining)
        if total_w == 0:
            continue

        adjusted = []
        for ind in remaining:
            new_ind = deepcopy(ind)
            new_ind.weight = ind.weight / total_w
            adjusted.append(new_ind)

        new_config = IndexConfig(
            indicators=adjusted,
            poverty_cutoff_k=config.poverty_cutoff_k,
            subgroup_column=config.subgroup_column,
        )

        g0 = build_deprivation_matrix(data, new_config)
        scores = compute_deprivation_scores(g0, new_config)
        _, censored_scores = apply_poverty_cutoff(g0, scores, new_config.poverty_cutoff_k)
        result = aggregate(censored_scores, new_config.poverty_cutoff_k)

        results.append(
            {
                "dropped_indicator": dropped.name,
                "H": result.H,
                "A": result.A,
                "M0": result.M0,
            }
        )

    return results


def run_robustness(
    data: pd.DataFrame, config: IndexConfig, n_weight_scenarios: int = 100
) -> RobustnessResult:
    """Run all robustness checks."""
    return RobustnessResult(
        k_robustness=k_robustness(data, config),
        weight_robustness=weight_robustness(data, config, n_weight_scenarios),
        leave_one_out=leave_one_out(data, config),
    )
