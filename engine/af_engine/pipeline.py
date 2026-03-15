import pandas as pd
import numpy as np
from .types import IndexConfig, FullResults
from .identification import (
    build_deprivation_matrix,
    compute_deprivation_scores,
    apply_poverty_cutoff,
)
from .aggregation import aggregate
from .decomposition import dimensional_breakdown, subgroup_decomposition
from .robustness import run_robustness


def compute_index(
    data: pd.DataFrame,
    config: IndexConfig,
    include_robustness: bool = False,
    include_matrices: bool = False,
) -> FullResults:
    """Full AF method pipeline: identification -> aggregation -> decomposition."""
    # Validate
    total_weight = sum(ind.weight for ind in config.indicators)
    if not np.isclose(total_weight, 1.0, atol=1e-6):
        raise ValueError(f"Indicator weights must sum to 1.0, got {total_weight}")

    if not (0 < config.poverty_cutoff_k <= 1):
        raise ValueError(
            f"Poverty cutoff k must be in (0, 1], got {config.poverty_cutoff_k}"
        )

    # Step 1: Identification
    g0 = build_deprivation_matrix(data, config)
    scores = compute_deprivation_scores(g0, config)
    censored_g0, censored_scores = apply_poverty_cutoff(
        g0, scores, config.poverty_cutoff_k
    )

    # Step 2: Aggregation
    headline = aggregate(censored_scores, config.poverty_cutoff_k)

    # Step 3: Dimensional breakdown
    dim_breakdown = dimensional_breakdown(g0, censored_g0, config, headline.M0)

    # Step 4: Subgroup decomposition (if configured)
    subgroups = None
    if config.subgroup_column and config.subgroup_column in data.columns:
        subgroups = subgroup_decomposition(
            censored_scores,
            data[config.subgroup_column].values,
            config.poverty_cutoff_k,
            headline.M0,
        )

    # Step 5: Robustness (optional)
    robustness = None
    if include_robustness:
        robustness = run_robustness(data, config)

    return FullResults(
        headline=headline,
        dimensional_breakdown=dim_breakdown,
        subgroup_results=subgroups,
        robustness=robustness,
        deprivation_matrix=g0 if include_matrices else None,
        censored_matrix=censored_g0 if include_matrices else None,
        deprivation_scores=scores if include_matrices else None,
        censored_scores=censored_scores if include_matrices else None,
    )
