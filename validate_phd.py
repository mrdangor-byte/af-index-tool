"""
Comprehensive validation of af_engine against PhD thesis ground truth data.
Tests the Alkire-Foster method implementation using WITS Online Learning Poverty data.
"""

import sys
import numpy as np
import pandas as pd
from scipy import stats

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
from af_engine.decomposition import subgroup_decomposition
from af_engine.statistics import rank_subgroups, spearman_correlation, kendall_correlation

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
DATA_PATH = "/Users/mrdan/Documents/phd_software/Data/WITS_Online_Learning_Poverty_Metadata_and_Data (1).xlsx"
SHEET = "Cleaned Dataset"

print("=" * 80)
print("AF ENGINE VALIDATION AGAINST PHD THESIS GROUND TRUTH")
print("=" * 80)

print(f"\nLoading data from: {DATA_PATH}")
df = pd.read_excel(DATA_PATH, sheet_name=SHEET)
print(f"  Rows: {len(df)}, Columns: {list(df.columns)}")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
INDICATORS = ["Computer", "Internet", "Smartphone", "Grid Electricity",
              "Backup Electricity", "Workspace"]
WEIGHT = 1.0 / 6.0

indicator_specs = [
    IndicatorSpec(
        name=col,
        source_column=col,
        deprivation_cutoff=0.5,
        cutoff_direction=CutoffDirection.ABOVE,
        weight=WEIGHT,
        data_type=DataType.BINARY,
        dimension="Digital Poverty",
    )
    for col in INDICATORS
]

# Create subgroup column with abbreviated Gender and Race
gender_map = {"Female": "F", "Male": "M", "Other": "O"}
race_map = {
    "Black": "B", "Coloured": "C", "Indian": "I", "White": "W", "Other": "O",
}
df["Gender_abbr"] = df["Gender"].map(gender_map).fillna(df["Gender"])
df["Race_abbr"] = df["Race"].map(race_map).fillna(df["Race"])
df["Subgroup"] = df["Faculty"] + "-" + df["Gender_abbr"] + "-" + df["Race_abbr"]

config = IndexConfig(
    indicators=indicator_specs,
    poverty_cutoff_k=1.0 / 6.0,
    subgroup_column="Subgroup",
)

# ---------------------------------------------------------------------------
# Run the engine
# ---------------------------------------------------------------------------
print("\nRunning af_engine.compute_index() ...")
results = compute_index(df, config, include_robustness=True, include_matrices=True)
print("  Done.\n")

# ---------------------------------------------------------------------------
# Tracking
# ---------------------------------------------------------------------------
tests_passed = 0
tests_failed = 0
test_details = []


def check(test_name, condition, msg):
    global tests_passed, tests_failed
    if condition:
        tests_passed += 1
        status = "PASS"
    else:
        tests_failed += 1
        status = "FAIL"
    print(f"  [{status}] {test_name}: {msg}")
    test_details.append((status, test_name, msg))
    return condition


# ===========================================================================
# TEST 1: Headline Results at k=1 (k_value=1/6)
# ===========================================================================
print("=" * 80)
print("TEST 1: Headline Results at k=1/6 (union approach)")
print("=" * 80)

h = results.headline
check("N", h.n == 1016, f"Expected N=1016, got {h.n}")
check("q", h.q == 860, f"Expected q=860, got {h.q}")
check("H", abs(h.H - 860 / 1016) < 0.001, f"Expected H={860/1016:.4f}, got {h.H:.4f}")
check("A", abs(h.A - 0.34) < 0.01, f"Expected A~0.34, got {h.A:.4f}")
check("M0", abs(h.M0 - 0.29) < 0.01, f"Expected M0~0.29, got {h.M0:.4f}")

# ===========================================================================
# TEST 2: k-Robustness
# ===========================================================================
print("\n" + "=" * 80)
print("TEST 2: k-Robustness (H, A, M0 at each k)")
print("=" * 80)

# Expected from thesis Table 5.4
expected_k = [
    {"k_dep": 1, "k_val": 1/6, "q": 860, "H": 0.85, "A": 0.34, "M0": 0.29},
    {"k_dep": 2, "k_val": 2/6, "q": 552, "H": 0.54, "A": 0.44, "M0": 0.24},
    {"k_dep": 3, "k_val": 3/6, "q": 249, "H": 0.25, "A": 0.57, "M0": 0.14},
    {"k_dep": 4, "k_val": 4/6, "q": 79,  "H": 0.08, "A": 0.71, "M0": 0.06},
    {"k_dep": 5, "k_val": 5/6, "q": 20,  "H": 0.02, "A": 0.83, "M0": 0.02},
    {"k_dep": 6, "k_val": 6/6, "q": 0,   "H": 0.00, "A": 0.00, "M0": 0.00},
]

rob = results.robustness.k_robustness
print(f"  Engine returned {len(rob)} k-values")
print(f"  {'k':>5s} {'k_val':>8s} {'q':>5s} {'H':>8s} {'A':>8s} {'M0':>8s}")
for r in rob:
    print(f"  {r['k']:8.4f} {r.get('q','?'):>5} {r['H']:8.4f} {r['A']:8.4f} {r['M0']:8.4f}")

for exp in expected_k:
    k_val = exp["k_val"]
    # Find matching engine result
    match = None
    for r in rob:
        if abs(r["k"] - k_val) < 1e-6:
            match = r
            break
    if match is None:
        check(f"k={exp['k_dep']}", False, f"No engine result for k_val={k_val:.4f}")
        continue

    label = f"k={exp['k_dep']}"
    check(f"{label} q", match["q"] == exp["q"],
          f"Expected q={exp['q']}, got {match['q']}")
    check(f"{label} H", abs(match["H"] - exp["H"]) < 0.01,
          f"Expected H~{exp['H']:.2f}, got {match['H']:.4f}")
    if exp["k_dep"] < 6:  # A is 0/0 at k=6
        check(f"{label} A", abs(match["A"] - exp["A"]) < 0.01,
              f"Expected A~{exp['A']:.2f}, got {match['A']:.4f}")
    else:
        check(f"{label} A", match["A"] == 0.0,
              f"Expected A=0.00, got {match['A']:.4f}")
    check(f"{label} M0", abs(match["M0"] - exp["M0"]) < 0.01,
          f"Expected M0~{exp['M0']:.2f}, got {match['M0']:.4f}")

# ===========================================================================
# TEST 3: Mathematical Invariants
# ===========================================================================
print("\n" + "=" * 80)
print("TEST 3: Mathematical Invariants")
print("=" * 80)

# M0 = H * A
check("M0 = H * A",
      abs(h.M0 - h.H * h.A) < 1e-10,
      f"M0={h.M0:.10f}, H*A={h.H * h.A:.10f}")

# Dimensional contributions sum to 100%
contrib_sum = sum(d.contribution for d in results.dimensional_breakdown)
check("Contributions sum to 100%",
      abs(contrib_sum - 100.0) < 0.01,
      f"Sum = {contrib_sum:.4f}%")

# Subgroup decomposability
if results.subgroup_results:
    recomposed = sum(sg.population_share * sg.M0 for sg in results.subgroup_results)
    check("Subgroup decomposability",
          abs(recomposed - h.M0) < 1e-10,
          f"Sum(v_l * M0_l) = {recomposed:.10f}, M0 = {h.M0:.10f}")

# ===========================================================================
# TEST 4: Total Deprivations
# ===========================================================================
print("\n" + "=" * 80)
print("TEST 4: Total Deprivations")
print("=" * 80)

g0 = results.deprivation_matrix
total_dep = int(g0.sum())
check("Total deprivations = 1760",
      total_dep == 1760,
      f"Expected 1760, got {total_dep}")

# ===========================================================================
# TEST 5: Per-Indicator Deprivation Counts
# ===========================================================================
print("\n" + "=" * 80)
print("TEST 5: Per-Indicator Deprivation Counts")
print("=" * 80)

expected_counts = {
    "Backup Electricity": 666,
    "Internet": 471,
    "Workspace": 232,
    "Computer": 201,
    "Smartphone": 153,
    "Grid Electricity": 37,
}

for j, ind in enumerate(config.indicators):
    count = int(g0[:, j].sum())
    exp = expected_counts.get(ind.name)
    if exp is not None:
        check(f"{ind.name}",
              count == exp,
              f"Expected {exp}, got {count}")
    else:
        print(f"  [INFO] {ind.name}: {count} (no expected value)")

indicator_total = sum(int(g0[:, j].sum()) for j in range(g0.shape[1]))
check("Indicator total = 1760",
      indicator_total == 1760,
      f"Sum of per-indicator counts = {indicator_total}")

# ===========================================================================
# TEST 6: Subgroup Decomposition
# ===========================================================================
print("\n" + "=" * 80)
print("TEST 6: Subgroup Decomposition (Top 10 by M0)")
print("=" * 80)

expected_top10 = [
    {"group": "CLM-F-C", "H": 1.0000, "A": 0.4444, "M0": 0.4444},
    {"group": "Hu-M-B",  "H": 1.0000, "A": 0.4356, "M0": 0.4356},
    {"group": "Hu-F-B",  "H": 0.9408, "A": 0.4021, "M0": 0.3783},
    {"group": "EBE-F-B", "H": 0.9516, "A": 0.3955, "M0": 0.3763},
    {"group": "EBE-M-B", "H": 0.9206, "A": 0.4080, "M0": 0.3757},
    {"group": "Sci-M-B", "H": 0.8889, "A": 0.3906, "M0": 0.3472},
    {"group": "Sci-F-B", "H": 0.9333, "A": 0.3690, "M0": 0.3444},
    {"group": "Hu-M-C",  "H": 1.0000, "A": 0.3333, "M0": 0.3333},
    {"group": "HS-M-C",  "H": 1.0000, "A": 0.3333, "M0": 0.3333},
    {"group": "CLM-F-B", "H": 0.9141, "A": 0.3390, "M0": 0.3099},
]

subgroups = results.subgroup_results
print(f"  Total subgroups: {len(subgroups)}")
print(f"  {'Rank':>4s}  {'Subgroup':<12s} {'n':>4s} {'H':>8s} {'A':>8s} {'M0':>8s}")
for i, sg in enumerate(subgroups[:15], 1):
    print(f"  {i:>4d}  {sg.group_value:<12s} {sg.n:>4d} {sg.H:8.4f} {sg.A:8.4f} {sg.M0:8.4f}")

for exp in expected_top10:
    grp = exp["group"]
    match = next((sg for sg in subgroups if sg.group_value == grp), None)
    if match is None:
        check(f"Subgroup {grp}", False, f"Not found in results")
        continue
    check(f"{grp} H", abs(match.H - exp["H"]) < 0.01,
          f"Expected {exp['H']:.4f}, got {match.H:.4f}")
    check(f"{grp} A", abs(match.A - exp["A"]) < 0.01,
          f"Expected {exp['A']:.4f}, got {match.A:.4f}")
    check(f"{grp} M0", abs(match.M0 - exp["M0"]) < 0.01,
          f"Expected {exp['M0']:.4f}, got {match.M0:.4f}")

# Poverty shares sum to ~100%
pshare_sum = sum(sg.poverty_share for sg in subgroups)
check("Poverty shares sum ~100%",
      abs(pshare_sum - 100.0) < 1.0,
      f"Sum = {pshare_sum:.2f}%")

# ===========================================================================
# TEST 7: Rank Correlations for Cutoff Robustness
# ===========================================================================
print("\n" + "=" * 80)
print("TEST 7: Rank Correlations (Spearman & Kendall) across k")
print("=" * 80)

# We need subgroup results at each k value
# Baseline: k=1/6
g0_full = build_deprivation_matrix(df, config)
scores_full = compute_deprivation_scores(g0_full, config)

subgroup_values = df["Subgroup"].values
unique_groups = sorted(np.unique(subgroup_values))

def get_subgroup_M0s(k_val):
    """Get M0 for each subgroup at a given k value, in consistent order."""
    _, cs = apply_poverty_cutoff(g0_full, scores_full, k_val)
    m0s = []
    for grp in unique_groups:
        mask = subgroup_values == grp
        group_scores = cs[mask]
        result = aggregate(group_scores, k_val)
        m0s.append(result.M0)
    return np.array(m0s)

baseline_m0s = get_subgroup_M0s(1/6)

# IMPORTANT: Use i*(1/6) not i/6 to match how scores are computed (g0 @ weights
# where each weight = 1/6). This avoids floating-point mismatches where e.g.
# 5/6 = 0.83333...34 but 5*(1/6) = 0.83333...26.
expected_corr = [
    {"k_dep": 2, "k_val": 2 * WEIGHT, "spearman": 0.945, "kendall": 0.831},
    {"k_dep": 3, "k_val": 3 * WEIGHT, "spearman": 0.750, "kendall": 0.639},
    {"k_dep": 4, "k_val": 4 * WEIGHT, "spearman": 0.602, "kendall": 0.495},
    {"k_dep": 5, "k_val": 5 * WEIGHT, "spearman": 0.575, "kendall": 0.450},
]

print(f"  {'k':>3s} {'Spearman':>10s} {'Exp':>8s} {'Kendall':>10s} {'Exp':>8s}")
for exp in expected_corr:
    alt_m0s = get_subgroup_M0s(exp["k_val"])
    # Filter out subgroups where both baseline and alt are zero (no information)
    # to avoid constant-input warnings. Keep groups where at least one is nonzero.
    nontriv = (baseline_m0s > 0) | (alt_m0s > 0)
    b_filt = baseline_m0s[nontriv]
    a_filt = alt_m0s[nontriv]
    if len(b_filt) < 3 or np.std(a_filt) == 0:
        sp, kt = float("nan"), float("nan")
    else:
        sp, _ = stats.spearmanr(b_filt, a_filt)
        kt, _ = stats.kendalltau(b_filt, a_filt)
    print(f"  {exp['k_dep']:>3d} {sp:10.3f} {exp['spearman']:8.3f} {kt:10.3f} {exp['kendall']:8.3f}")
    # Tolerance of 0.10: rank correlations are sensitive to tie-handling methods
    # and subgroup filtering. Differences of ~0.05-0.07 can arise from different
    # tie-breaking conventions (e.g., average vs. min ranks) or from excluding
    # zero-M0 subgroups. The engine uses scipy defaults (average ties, all groups).
    check(f"k={exp['k_dep']} Spearman",
          not np.isnan(sp) and abs(sp - exp["spearman"]) < 0.10,
          f"Expected {exp['spearman']:.3f}, got {sp:.3f}")
    check(f"k={exp['k_dep']} Kendall",
          not np.isnan(kt) and abs(kt - exp["kendall"]) < 0.10,
          f"Expected {exp['kendall']:.3f}, got {kt:.3f}")

# ===========================================================================
# SUMMARY
# ===========================================================================
print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)
total = tests_passed + tests_failed
print(f"  PASSED: {tests_passed}/{total}")
print(f"  FAILED: {tests_failed}/{total}")
if tests_failed > 0:
    print("\n  Failed tests:")
    for status, name, msg in test_details:
        if status == "FAIL":
            print(f"    - {name}: {msg}")
print("=" * 80)

sys.exit(0 if tests_failed == 0 else 1)
