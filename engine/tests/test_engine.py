"""Comprehensive tests for the af_engine package."""

import numpy as np
import pandas as pd
import pytest

from af_engine import (
    IndexConfig,
    IndicatorSpec,
    CutoffDirection,
    DataType,
    compute_index,
)
from af_engine.identification import (
    build_deprivation_matrix,
    compute_deprivation_scores,
    apply_poverty_cutoff,
)
from af_engine.aggregation import aggregate
from af_engine.decomposition import dimensional_breakdown, subgroup_decomposition
from af_engine.robustness import k_robustness, leave_one_out, weight_robustness


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_data():
    """5 people, 3 indicators with equal weights (1/3 each).

    Indicators (all CutoffDirection.BELOW):
      - education: cutoff 6 (deprived if < 6)
      - health:    cutoff 1 (deprived if < 1, i.e. value == 0)
      - income:    cutoff 500

    Person | edu | health | income | deprived_edu | deprived_health | deprived_income | score
    -------|-----|--------|--------|--------------|-----------------|-----------------|------
    0      |  4  |   0    |  300   |      1       |        1        |        1        | 1.0
    1      |  8  |   1    |  200   |      0       |        0        |        1        | 1/3
    2      |  3  |   0    |  800   |      1       |        1        |        0        | 2/3
    3      | 10  |   1    | 1000   |      0       |        0        |        0        | 0.0
    4      |  5  |   0    |  400   |      1       |        1        |        1        | 1.0
    """
    return pd.DataFrame({
        "education": [4, 8, 3, 10, 5],
        "health": [0, 1, 0, 1, 0],
        "income": [300, 200, 800, 1000, 400],
        "region": ["A", "A", "B", "B", "A"],
    })


@pytest.fixture
def equal_weight_config():
    """3 indicators with equal weight = 1/3."""
    return IndexConfig(
        indicators=[
            IndicatorSpec(
                name="Education",
                source_column="education",
                deprivation_cutoff=6,
                weight=1 / 3,
                dimension="Education",
            ),
            IndicatorSpec(
                name="Health",
                source_column="health",
                deprivation_cutoff=1,
                weight=1 / 3,
                dimension="Health",
            ),
            IndicatorSpec(
                name="Income",
                source_column="income",
                deprivation_cutoff=500,
                weight=1 / 3,
                dimension="Living Standards",
            ),
        ],
        poverty_cutoff_k=1 / 3,  # union approach: deprived in at least 1
    )


@pytest.fixture
def config_with_subgroup(equal_weight_config):
    equal_weight_config.subgroup_column = "region"
    return equal_weight_config


# ---------------------------------------------------------------------------
# Basic identification tests
# ---------------------------------------------------------------------------

class TestIdentification:
    def test_deprivation_matrix_shape(self, synthetic_data, equal_weight_config):
        g0 = build_deprivation_matrix(synthetic_data, equal_weight_config)
        assert g0.shape == (5, 3)

    def test_deprivation_matrix_values(self, synthetic_data, equal_weight_config):
        g0 = build_deprivation_matrix(synthetic_data, equal_weight_config)
        # Person 0: deprived in all 3
        np.testing.assert_array_equal(g0[0], [1, 1, 1])
        # Person 1: deprived only in income
        np.testing.assert_array_equal(g0[1], [0, 0, 1])
        # Person 3: not deprived at all
        np.testing.assert_array_equal(g0[3], [0, 0, 0])

    def test_deprivation_scores(self, synthetic_data, equal_weight_config):
        g0 = build_deprivation_matrix(synthetic_data, equal_weight_config)
        scores = compute_deprivation_scores(g0, equal_weight_config)
        expected = np.array([1.0, 1 / 3, 2 / 3, 0.0, 1.0])
        np.testing.assert_allclose(scores, expected, atol=1e-10)

    def test_poverty_cutoff_union(self, synthetic_data, equal_weight_config):
        """k=1/3 means anyone deprived in >= 1 indicator is identified."""
        g0 = build_deprivation_matrix(synthetic_data, equal_weight_config)
        scores = compute_deprivation_scores(g0, equal_weight_config)
        censored_g0, censored_scores = apply_poverty_cutoff(g0, scores, 1 / 3)
        # Person 3 has score 0, should be censored
        np.testing.assert_array_equal(censored_g0[3], [0, 0, 0])
        assert censored_scores[3] == 0.0
        # Person 1 has score 1/3, should still be identified
        assert censored_scores[1] == pytest.approx(1 / 3)


# ---------------------------------------------------------------------------
# CutoffDirection.ABOVE tests
# ---------------------------------------------------------------------------

class TestCutoffAbove:
    def test_above_direction(self):
        """Test that ABOVE direction correctly identifies deprivation."""
        data = pd.DataFrame({"pollution": [10, 50, 100, 5, 80]})
        config = IndexConfig(
            indicators=[
                IndicatorSpec(
                    name="Pollution",
                    source_column="pollution",
                    deprivation_cutoff=40,
                    cutoff_direction=CutoffDirection.ABOVE,
                    weight=1.0,
                )
            ],
            poverty_cutoff_k=1.0,
        )
        g0 = build_deprivation_matrix(data, config)
        # Deprived if pollution > 40: persons 1(50), 2(100), 4(80)
        expected = np.array([[0], [1], [1], [0], [1]], dtype=np.float64)
        np.testing.assert_array_equal(g0, expected)

    def test_above_in_full_pipeline(self):
        data = pd.DataFrame({
            "pollution": [10, 50, 100, 5, 80],
            "noise": [30, 70, 20, 90, 60],
        })
        config = IndexConfig(
            indicators=[
                IndicatorSpec(
                    name="Pollution",
                    source_column="pollution",
                    deprivation_cutoff=40,
                    cutoff_direction=CutoffDirection.ABOVE,
                    weight=0.5,
                ),
                IndicatorSpec(
                    name="Noise",
                    source_column="noise",
                    deprivation_cutoff=50,
                    cutoff_direction=CutoffDirection.ABOVE,
                    weight=0.5,
                ),
            ],
            poverty_cutoff_k=0.5,
        )
        result = compute_index(data, config)
        # Pollution deprived: 1,2,4  Noise deprived: 1,3,4
        # Scores: [0, 1.0, 0.5, 0.5, 1.0]
        # All with score >= 0.5 are identified: persons 1,2,3,4
        assert result.headline.q == 4
        assert result.headline.n == 5


# ---------------------------------------------------------------------------
# M0 = H * A invariant
# ---------------------------------------------------------------------------

class TestM0Invariant:
    def test_M0_equals_H_times_A(self, synthetic_data, equal_weight_config):
        result = compute_index(synthetic_data, equal_weight_config)
        assert result.headline.M0 == pytest.approx(
            result.headline.H * result.headline.A, abs=1e-10
        )

    def test_M0_invariant_various_k(self, synthetic_data, equal_weight_config):
        """Check H*A = M0 for several k values."""
        for k in [1 / 3, 2 / 3, 1.0]:
            equal_weight_config.poverty_cutoff_k = k
            result = compute_index(synthetic_data, equal_weight_config)
            assert result.headline.M0 == pytest.approx(
                result.headline.H * result.headline.A, abs=1e-10
            ), f"Failed for k={k}"


# ---------------------------------------------------------------------------
# Contributions sum to 100%
# ---------------------------------------------------------------------------

class TestContributions:
    def test_contributions_sum_to_100(self, synthetic_data, equal_weight_config):
        result = compute_index(synthetic_data, equal_weight_config)
        total_contrib = sum(d.contribution for d in result.dimensional_breakdown)
        assert total_contrib == pytest.approx(100.0, abs=1e-6)

    def test_absolute_contributions_sum_to_M0(self, synthetic_data, equal_weight_config):
        result = compute_index(synthetic_data, equal_weight_config)
        total_abs = sum(d.absolute_contribution for d in result.dimensional_breakdown)
        assert total_abs == pytest.approx(result.headline.M0, abs=1e-10)


# ---------------------------------------------------------------------------
# Subgroup decomposability: sum(v_l * M0_l) = M0
# ---------------------------------------------------------------------------

class TestSubgroupDecomposability:
    def test_decomposability(self, synthetic_data, config_with_subgroup):
        result = compute_index(synthetic_data, config_with_subgroup)
        assert result.subgroup_results is not None

        weighted_sum = sum(
            sg.population_share * sg.M0 for sg in result.subgroup_results
        )
        assert weighted_sum == pytest.approx(result.headline.M0, abs=1e-10)

    def test_poverty_shares_sum_to_100(self, synthetic_data, config_with_subgroup):
        result = compute_index(synthetic_data, config_with_subgroup)
        total_share = sum(sg.poverty_share for sg in result.subgroup_results)
        assert total_share == pytest.approx(100.0, abs=1e-6)

    def test_population_shares_sum_to_1(self, synthetic_data, config_with_subgroup):
        result = compute_index(synthetic_data, config_with_subgroup)
        total_pop = sum(sg.population_share for sg in result.subgroup_results)
        assert total_pop == pytest.approx(1.0, abs=1e-10)


# ---------------------------------------------------------------------------
# k-robustness
# ---------------------------------------------------------------------------

class TestKRobustness:
    def test_returns_results_for_all_valid_k(self, synthetic_data, equal_weight_config):
        results = k_robustness(synthetic_data, equal_weight_config)
        assert len(results) > 0
        # With weights 1/3 each, valid k values are 1/3, 2/3, 1.0
        k_values = [r["k"] for r in results]
        assert pytest.approx(1 / 3, abs=1e-8) in k_values
        assert pytest.approx(2 / 3, abs=1e-8) in k_values
        assert pytest.approx(1.0, abs=1e-8) in k_values

    def test_M0_decreases_with_k(self, synthetic_data, equal_weight_config):
        """M0 should be non-increasing as k increases."""
        results = k_robustness(synthetic_data, equal_weight_config)
        m0_values = [r["M0"] for r in results]
        for i in range(1, len(m0_values)):
            assert m0_values[i] <= m0_values[i - 1] + 1e-10

    def test_H_decreases_with_k(self, synthetic_data, equal_weight_config):
        """H should be non-increasing as k increases."""
        results = k_robustness(synthetic_data, equal_weight_config)
        h_values = [r["H"] for r in results]
        for i in range(1, len(h_values)):
            assert h_values[i] <= h_values[i - 1] + 1e-10


# ---------------------------------------------------------------------------
# Leave-one-out
# ---------------------------------------------------------------------------

class TestLeaveOneOut:
    def test_drops_one_indicator_at_a_time(self, synthetic_data, equal_weight_config):
        results = leave_one_out(synthetic_data, equal_weight_config)
        assert len(results) == 3
        dropped_names = {r["dropped_indicator"] for r in results}
        assert dropped_names == {"Education", "Health", "Income"}

    def test_leave_one_out_has_valid_values(self, synthetic_data, equal_weight_config):
        results = leave_one_out(synthetic_data, equal_weight_config)
        for r in results:
            assert 0 <= r["H"] <= 1
            assert 0 <= r["M0"] <= 1
            assert 0 <= r["A"] <= 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_deprived(self):
        """Everyone is deprived in all indicators."""
        data = pd.DataFrame({
            "x": [0, 0, 0, 0],
            "y": [0, 0, 0, 0],
        })
        config = IndexConfig(
            indicators=[
                IndicatorSpec(name="X", source_column="x", deprivation_cutoff=1, weight=0.5),
                IndicatorSpec(name="Y", source_column="y", deprivation_cutoff=1, weight=0.5),
            ],
            poverty_cutoff_k=0.5,
        )
        result = compute_index(data, config)
        assert result.headline.H == 1.0
        assert result.headline.A == 1.0
        assert result.headline.M0 == 1.0
        assert result.headline.q == 4
        assert result.headline.n == 4

    def test_none_deprived(self):
        """Nobody is deprived."""
        data = pd.DataFrame({
            "x": [10, 10, 10],
            "y": [10, 10, 10],
        })
        config = IndexConfig(
            indicators=[
                IndicatorSpec(name="X", source_column="x", deprivation_cutoff=5, weight=0.5),
                IndicatorSpec(name="Y", source_column="y", deprivation_cutoff=5, weight=0.5),
            ],
            poverty_cutoff_k=0.5,
        )
        result = compute_index(data, config)
        assert result.headline.H == 0.0
        assert result.headline.A == 0.0
        assert result.headline.M0 == 0.0
        assert result.headline.q == 0

    def test_k_equals_1_intersection(self):
        """k=1 means intersection: must be deprived in ALL indicators."""
        data = pd.DataFrame({
            "x": [0, 0, 5],
            "y": [0, 5, 0],
        })
        config = IndexConfig(
            indicators=[
                IndicatorSpec(name="X", source_column="x", deprivation_cutoff=1, weight=0.5),
                IndicatorSpec(name="Y", source_column="y", deprivation_cutoff=1, weight=0.5),
            ],
            poverty_cutoff_k=1.0,
        )
        result = compute_index(data, config)
        # Only person 0 is deprived in both
        assert result.headline.q == 1
        assert result.headline.H == pytest.approx(1 / 3)
        assert result.headline.A == 1.0
        assert result.headline.M0 == pytest.approx(1 / 3)


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

class TestValidation:
    def test_weights_must_sum_to_1(self, synthetic_data):
        config = IndexConfig(
            indicators=[
                IndicatorSpec(name="X", source_column="education", deprivation_cutoff=6, weight=0.5),
                IndicatorSpec(name="Y", source_column="health", deprivation_cutoff=1, weight=0.3),
            ],
            poverty_cutoff_k=0.5,
        )
        with pytest.raises(ValueError, match="weights must sum to 1.0"):
            compute_index(synthetic_data, config)

    def test_k_must_be_positive(self, synthetic_data):
        config = IndexConfig(
            indicators=[
                IndicatorSpec(name="X", source_column="education", deprivation_cutoff=6, weight=1.0),
            ],
            poverty_cutoff_k=0.0,
        )
        with pytest.raises(ValueError, match="Poverty cutoff k"):
            compute_index(synthetic_data, config)

    def test_k_must_not_exceed_1(self, synthetic_data):
        config = IndexConfig(
            indicators=[
                IndicatorSpec(name="X", source_column="education", deprivation_cutoff=6, weight=1.0),
            ],
            poverty_cutoff_k=1.5,
        )
        with pytest.raises(ValueError, match="Poverty cutoff k"):
            compute_index(synthetic_data, config)


# ---------------------------------------------------------------------------
# Full pipeline integration
# ---------------------------------------------------------------------------

class TestFullPipeline:
    def test_include_matrices(self, synthetic_data, equal_weight_config):
        result = compute_index(synthetic_data, equal_weight_config, include_matrices=True)
        assert result.deprivation_matrix is not None
        assert result.censored_matrix is not None
        assert result.deprivation_scores is not None
        assert result.censored_scores is not None
        assert result.deprivation_matrix.shape == (5, 3)

    def test_exclude_matrices_by_default(self, synthetic_data, equal_weight_config):
        result = compute_index(synthetic_data, equal_weight_config)
        assert result.deprivation_matrix is None
        assert result.censored_matrix is None

    def test_include_robustness(self, synthetic_data, equal_weight_config):
        result = compute_index(
            synthetic_data, equal_weight_config, include_robustness=True
        )
        assert result.robustness is not None
        assert len(result.robustness.k_robustness) > 0
        assert len(result.robustness.leave_one_out) == 3
        assert len(result.robustness.weight_robustness) == 100

    def test_known_values(self, synthetic_data, equal_weight_config):
        """Verify against hand-calculated values.

        With k=1/3 (union), identified persons: 0,1,2,4 (score >= 1/3).
        Person 3 has score 0 and is not identified.
        q=4, n=5, H=4/5=0.8
        Censored scores: [1.0, 1/3, 2/3, 0.0, 1.0]
        A = mean of identified scores = (1 + 1/3 + 2/3 + 1) / 4 = 3/4 = 0.75
        M0 = mean of all censored scores = (1 + 1/3 + 2/3 + 0 + 1) / 5 = 3/5 = 0.6
        Check: H*A = 0.8 * 0.75 = 0.6 = M0 ✓
        """
        result = compute_index(synthetic_data, equal_weight_config)
        assert result.headline.q == 4
        assert result.headline.n == 5
        assert result.headline.H == pytest.approx(0.8)
        assert result.headline.A == pytest.approx(0.75)
        assert result.headline.M0 == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Weight robustness
# ---------------------------------------------------------------------------

class TestWeightRobustness:
    def test_returns_correct_number_of_scenarios(self, synthetic_data, equal_weight_config):
        results = weight_robustness(synthetic_data, equal_weight_config, n_scenarios=10)
        assert len(results) == 10

    def test_all_M0_valid(self, synthetic_data, equal_weight_config):
        results = weight_robustness(synthetic_data, equal_weight_config, n_scenarios=20)
        for r in results:
            assert 0 <= r["M0"] <= 1
            assert 0 <= r["H"] <= 1
