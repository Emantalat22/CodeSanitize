import json
import urllib.request

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

print("=== Testing CodeSanitize Transformation Endpoints ===")

# 1. Test GET /api/transformations
s_rules, rules = get("http://127.0.0.1:8000/api/transformations")
print(f"1. GET /api/transformations -> Status: {s_rules}, Rules Count: {len(rules)}")
for r in rules:
    print(f"   - [{r['rule_id']}] {r['name']} ({r['safety_level']})")

# 2. Test Full Python Transformation
sample_code = """def compute_stats(values: list[float], scale: float = 1.0) -> dict:
    \"\"\"Calculate scaled statistics.\"\"\"
    temp_sum = 0.0   
    for single_val in values:
        intermediate_scaled = single_val * scale   
        temp_sum = temp_sum + intermediate_scaled


    calc_mean = ( temp_sum / len(values) ) if values else 0.0
    return {"sum": temp_sum, "mean": calc_mean}
"""

s_trans, r_trans = post("http://127.0.0.1:8000/api/transform", {
    "code": sample_code,
    "language": "python",
    "filename": "stats.py"
})

print(f"\n2. POST /api/transform -> Status: {s_trans}, Transformation Status: {r_trans['transformation_status']}, Validation: {r_trans['validation_status']}")
print(f"   - Applied Rules: {len(r_trans['transformations_applied'])}")
for t in r_trans['transformations_applied']:
    print(f"     * {t['name']} ({t['rule_id']}): {t['changes_description']}")
print(f"   - Total Change Count: {r_trans['change_count']}")
print(f"   - Diff Additions: +{r_trans['diff_summary']['additions']}, Removals: -{r_trans['diff_summary']['removals']}")

# 3. Test Invalid Python Code
s_err, r_err = post("http://127.0.0.1:8000/api/transform", {
    "code": "def broken(a, b)\n  return a + b\n",
    "language": "python"
})
print(f"\n3. Invalid Python Code -> Status: {s_err}, Status: {r_err['transformation_status']}, Validation: {r_err['validation_status']}")
print(f"   - Warning: {r_err['warnings'][0] if r_err['warnings'] else 'None'}")

# 4. Test Frontend Proxied Call
s_proxy, r_proxy = post("http://127.0.0.1:5173/api/transform", {
    "code": "def simple(x):\n    val = x * 2   \n    return val\n",
    "language": "python"
})
print(f"\n4. Frontend Proxied Transformation -> Status: {s_proxy}, Status: {r_proxy['transformation_status']}, Validation: {r_proxy['validation_status']}, Applied: {len(r_proxy['transformations_applied'])}")

print("\n=== Transformation Engine Verification Complete! ===")
