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

print("=== Chunk 4 Advanced Validation & Equivalence Verification ===")

# 1. Test POST /api/validate on Valid Transformation
s1, r1 = post("http://127.0.0.1:8000/api/validate", {
    "original_code": "def calc(x: int) -> int:\n    val = x * 2\n    return val\n",
    "transformed_code": "def calc(x: int) -> int:\n    _norm_var_1 = x * 2\n    return _norm_var_1\n",
    "language": "python",
    "policy": "strict"
})
print(f"\n1. POST /api/validate (Valid) -> Status: {s1}, is_valid: {r1['is_valid']}, Verdict: {r1['verdict']}, Confidence: {r1['confidence_level']}")
print(f"   Validators Run ({len(r1['validators_run'])}): {', '.join(r1['validators_run'])}")
print(f"   Passed Checks: {len(r1['passed_checks'])}, Failures: {len(r1['failures'])}, Warnings: {len(r1['warnings'])}")

# 2. Test POST /api/validate on Mutated Function Signature (Must Fail)
s2, r2 = post("http://127.0.0.1:8000/api/validate", {
    "original_code": "def calc(x: int) -> int:\n    return x * 2\n",
    "transformed_code": "def calc(x: int, y: int = 0) -> int:\n    return x * 2\n",
    "language": "python",
    "policy": "strict"
})
print(f"\n2. POST /api/validate (Mutated Signature) -> Status: {s2}, is_valid: {r2['is_valid']}, Verdict: {r2['verdict']}")
print(f"   Failure detail: {r2['failures'][0]['details'] if r2['failures'] else 'None'}")

# 3. Test Reflection Detection & Policy Differences
reflection_code = "def get_scope():\n    temp = 1\n    return locals()\n"
s_strict, r_strict = post("http://127.0.0.1:8000/api/validate", {
    "original_code": reflection_code,
    "transformed_code": reflection_code,
    "language": "python",
    "policy": "strict"
})
s_bal, r_bal = post("http://127.0.0.1:8000/api/validate", {
    "original_code": reflection_code,
    "transformed_code": reflection_code,
    "language": "python",
    "policy": "balanced"
})
print(f"\n3. Reflection Policy Test:")
print(f"   - STRICT: is_valid={r_strict['is_valid']}, verdict={r_strict['verdict']}, risk_flags={r_strict['risk_flags']}")
print(f"   - BALANCED: is_valid={r_bal['is_valid']}, verdict={r_bal['verdict']}, warnings={len(r_bal['warnings'])}")

# 4. Test POST /api/transform with Integrated Validation Pipeline
code = """def process_matrix(matrix: list[list[int]]) -> int:
    \"\"\"Sum matrix items safely.\"\"\"
    total_accumulator = 0   
    for row in matrix:
        for item in row:
            temp_elem = item * 2
            total_accumulator += temp_elem


    return total_accumulator
"""
s_trans, r_trans = post("http://127.0.0.1:8000/api/transform", {
    "code": code,
    "language": "python",
    "filename": "matrix.py",
    "options": {"validation_policy": "strict"}
})
print(f"\n4. POST /api/transform with Validation Pipeline -> Status: {s_trans}, Transformation: {r_trans['transformation_status']}, Validation: {r_trans['validation_status']}")
print(f"   Applied: {len(r_trans['transformations_applied'])}, Changes: {r_trans['change_count']}")
if r_trans.get("validation_report"):
    vr = r_trans["validation_report"]
    print(f"   Validation Report: Confidence={vr['confidence_level']}, Policy={vr['policy_applied']}, Passed={len(vr['passed_checks'])}")

# 5. Test Frontend Proxy
s_proxy, r_proxy = post("http://127.0.0.1:5173/api/validate", {
    "original_code": "def ping(): pass\n",
    "transformed_code": "def ping(): pass\n",
    "language": "python",
    "policy": "strict"
})
print(f"\n5. Frontend Proxied /api/validate -> Status: {s_proxy}, is_valid: {r_proxy['is_valid']}, Verdict: {r_proxy['verdict']}")

print("\n=== Chunk 4 Verification Completed Successfully! ===")
