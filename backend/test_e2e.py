"""End-to-end test of the full API with the PhD dataset."""
import sys
from pathlib import Path

# Add engine to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from fastapi.testclient import TestClient
from app.main import app
import os

# Clean up old DB
db_path = Path(__file__).resolve().parent / "af_index.db"
if db_path.exists():
    os.remove(db_path)

# Create tables
from app.database import Base, engine as db_engine
Base.metadata.create_all(bind=db_engine)

client = TestClient(app)
DATA_FILE = "/Users/mrdan/Documents/phd_software/Data/WITS_Online_Learning_Poverty_Metadata_and_Data (1).xlsx"

# 1. Sign up
print("=== SIGNUP ===")
r = client.post("/api/auth/signup", json={
    "email": "test@wits.ac.za",
    "password": "test1234",
    "full_name": "Test User",
    "institution": "Wits"
})
print(f"  Status: {r.status_code}")
assert r.status_code == 201, f"Signup failed: {r.text}"

# 2. Login
print("=== LOGIN ===")
r = client.post("/api/auth/login", json={
    "email": "test@wits.ac.za",
    "password": "test1234"
})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"  Token obtained")

# 3. Create project
print("=== CREATE PROJECT ===")
r = client.post("/api/projects", json={"name": "OLPI Validation"}, headers=headers)
assert r.status_code == 201, f"Create project failed: {r.text}"
project_id = r.json()["id"]
print(f"  Project ID: {project_id}")

# 4. Upload dataset
print("=== UPLOAD DATASET ===")
with open(DATA_FILE, "rb") as f:
    r = client.post(
        f"/api/projects/{project_id}/upload",
        files={"file": ("OLPI.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=headers
    )
assert r.status_code == 201, f"Upload failed: {r.text}"
upload_data = r.json()
print(f"  Rows: {upload_data['row_count']}")
print(f"  Columns: {[c['name'] for c in upload_data['column_metadata']]}")
assert upload_data["row_count"] == 1016, f"Expected 1016 rows, got {upload_data['row_count']}"

# 5. Configure index
print("=== CONFIGURE INDEX ===")
w = 1/6
config = {
    "poverty_cutoff_k": w,
    "subgroup_column": "Faculty-Gender-Race",
    "dimensions": [
        {
            "name": "Digital",
            "indicators": [
                {"name": "Internet", "source_column": "Internet", "deprivation_cutoff": 0.5, "cutoff_direction": "above", "weight": w, "data_type": "binary"},
                {"name": "Computer", "source_column": "Computer", "deprivation_cutoff": 0.5, "cutoff_direction": "above", "weight": w, "data_type": "binary"},
                {"name": "Smartphone", "source_column": "Smartphone", "deprivation_cutoff": 0.5, "cutoff_direction": "above", "weight": w, "data_type": "binary"},
            ]
        },
        {
            "name": "Energy",
            "indicators": [
                {"name": "Grid Electricity", "source_column": "Grid Electricity", "deprivation_cutoff": 0.5, "cutoff_direction": "above", "weight": w, "data_type": "binary"},
                {"name": "Backup Electricity", "source_column": "Backup Electricity", "deprivation_cutoff": 0.5, "cutoff_direction": "above", "weight": w, "data_type": "binary"},
            ]
        },
        {
            "name": "Learning Environment",
            "indicators": [
                {"name": "Workspace", "source_column": "Workspace", "deprivation_cutoff": 0.5, "cutoff_direction": "above", "weight": w, "data_type": "binary"},
            ]
        },
    ]
}
r = client.post(f"/api/projects/{project_id}/configuration", json=config, headers=headers)
assert r.status_code in (200, 201), f"Configure failed: {r.text}"
print(f"  Config saved: k={config['poverty_cutoff_k']:.4f}")

# 6. Run analysis
print("=== RUN ANALYSIS ===")
r = client.post(f"/api/projects/{project_id}/analyze", headers=headers)
assert r.status_code == 200, f"Analysis failed: {r.text}"
results = r.json()

H = results["H"]
A = results["A"]
M0 = results["M0"]
q = results["q"]
n = results["n"]

print(f"  H  = {H:.4f}  (expected 0.8465)")
print(f"  A  = {A:.4f}  (expected 0.3411)")
print(f"  M0 = {M0:.4f}  (expected 0.2887)")
print(f"  q  = {q}     (expected 860)")
print(f"  n  = {n}    (expected 1016)")

# Validate against thesis
PASS = 0
FAIL = 0

def check(name, actual, expected, tol=0.005):
    global PASS, FAIL
    if abs(actual - expected) <= tol:
        print(f"  PASS {name}: {actual:.4f} ≈ {expected:.4f}")
        PASS += 1
    else:
        print(f"  FAIL {name}: {actual:.4f} != {expected:.4f} (diff={abs(actual-expected):.4f})")
        FAIL += 1

check("H", H, 860/1016)
check("A", A, 0.3411, 0.005)
check("M0", M0, 0.2887, 0.005)

if q == 860:
    print(f"  PASS q = 860")
    PASS += 1
else:
    print(f"  FAIL q = {q} (expected 860)")
    FAIL += 1

if n == 1016:
    print(f"  PASS n = 1016")
    PASS += 1
else:
    print(f"  FAIL n = {n} (expected 1016)")
    FAIL += 1

# Check M0 = H * A
check("M0=H*A", M0, H * A, 0.0001)

# 7. Check dimensional breakdown
print("\n=== DIMENSIONAL BREAKDOWN ===")
breakdown = results["dimensional_breakdown"]
total_contribution = sum(d["contribution"] for d in breakdown)
check("Contributions sum to 100%", total_contribution, 100.0, 0.1)

for d in breakdown:
    print(f"  {d['indicator_name']}: contribution={d['contribution']:.1f}%, censored_hc={d['censored_headcount']:.4f}")

# 8. Check subgroup decomposition
print("\n=== SUBGROUP DECOMPOSITION ===")
subgroups = results.get("subgroup_decomposition")
if subgroups:
    print(f"  {len(subgroups)} subgroups found")
    # Check top 5
    for s in subgroups[:5]:
        print(f"  {s['group_value']}: M0={s['M0']:.4f}, H={s['H']:.4f}, A={s['A']:.4f}, pov_share={s['poverty_share']:.2f}%")

    # Check decomposability: sum(v_l * M0_l) = M0
    weighted_sum = sum(s["population_share"] * s["M0"] for s in subgroups)
    check("Subgroup decomposability", weighted_sum, M0, 0.001)

    # Check poverty shares sum to ~100%
    total_pov_share = sum(s["poverty_share"] for s in subgroups)
    check("Poverty shares sum to 100%", total_pov_share, 100.0, 1.0)
else:
    print("  WARNING: No subgroup results returned")
    FAIL += 1

# 9. Get stored results
print("\n=== GET STORED RESULTS ===")
r = client.get(f"/api/projects/{project_id}/results", headers=headers)
assert r.status_code == 200
stored = r.json()
check("Stored M0 matches", stored["M0"], M0, 0.0001)

# 10. Run robustness analysis
print("\n=== ROBUSTNESS ANALYSIS ===")
r = client.post(f"/api/projects/{project_id}/robustness", headers=headers)
assert r.status_code == 200, f"Robustness failed: {r.text}"
rob = r.json()

print(f"  k-robustness: {len(rob['k_robustness'])} k-values tested")
for kr in rob["k_robustness"]:
    print(f"    k={kr['k']:.4f}: H={kr['H']:.4f}, A={kr['A']:.4f}, M0={kr['M0']:.4f}, q={kr['q']}")

# Validate k-robustness against thesis
expected_k = [
    (1/6, 860, 0.85, 0.34, 0.29),
    (2/6, 552, 0.54, 0.44, 0.24),
    (3/6, 249, 0.25, 0.57, 0.14),
    (4/6, 79, 0.08, 0.71, 0.06),
    (5/6, 20, 0.02, 0.83, 0.02),
]

for k_val, exp_q, exp_H, exp_A, exp_M0 in expected_k:
    # Find matching k in results
    match = None
    for kr in rob["k_robustness"]:
        if abs(kr["k"] - k_val) < 0.01:
            match = kr
            break
    if match:
        check(f"k={k_val:.3f} H", match["H"], exp_H, 0.01)
        check(f"k={k_val:.3f} M0", match["M0"], exp_M0, 0.01)
        if match["q"] == exp_q:
            PASS += 1
        else:
            print(f"  FAIL k={k_val:.3f} q: {match['q']} != {exp_q}")
            FAIL += 1
    else:
        print(f"  FAIL: k={k_val:.3f} not found in results")
        FAIL += 1

if rob.get("leave_one_out"):
    print(f"\n  Leave-one-out: {len(rob['leave_one_out'])} tests")
    for loo in rob["leave_one_out"]:
        print(f"    Drop {loo['dropped_indicator']}: M0={loo['M0']:.4f}")

# 11. Export CSV
print("\n=== EXPORT CSV ===")
r = client.get(f"/api/projects/{project_id}/export/csv", headers=headers)
if r.status_code == 200:
    print(f"  CSV export: {len(r.content)} bytes")
    PASS += 1
else:
    print(f"  CSV export failed: {r.status_code} {r.text}")
    FAIL += 1

# Summary
print(f"\n{'='*50}")
print(f"RESULTS: {PASS} PASSED, {FAIL} FAILED")
print(f"{'='*50}")
