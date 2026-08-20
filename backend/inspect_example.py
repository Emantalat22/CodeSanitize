import ast
import json
import urllib.request

example_code = """def compute_stats(values: list[float], scale: float = 1.0) -> dict:
    \"\"\"Calculate scaled statistics.\"\"\"
    temp_sum = 0.0   
    for single_val in values:
        intermediate_scaled = single_val * scale   
        temp_sum = temp_sum + intermediate_scaled


    calc_mean = ( temp_sum / len(values) ) if values else 0.0
    return {"sum": temp_sum, "mean": calc_mean}
"""

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/transform",
    data=json.dumps({"code": example_code, "language": "python", "filename": "stats.py"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    res_json = json.loads(resp.read().decode())

print("=== RAW JSON RESPONSE ===")
print("Transformation Status:", res_json["transformation_status"])
print("Validation Status:", res_json["validation_status"])
print("Transformations Applied:", [t["rule_id"] for t in res_json["transformations_applied"]])

transformed_code = res_json["transformed_code"]

print("\n=== EXACT TRANSFORMED CODE (PRESERVING INDENTATION) ===")
print(repr(transformed_code))
print("\n--- PRINTED TRANSFORMED CODE ---")
print(transformed_code)
print("--------------------------------")

print("\n=== INDEPENDENT AST.PARSE CHECK ===")
try:
    parsed_ast = ast.parse(transformed_code)
    print("ast.parse SUCCESS: True")
except Exception as e:
    print(f"ast.parse FAILED: {e}")

print("\n=== INDEPENDENT COMPILE(..., mode='exec') CHECK ===")
try:
    compiled_code = compile(transformed_code, "<test>", "exec")
    print("compile() SUCCESS: True")
except Exception as e:
    print(f"compile() FAILED: {e}")

print("\n=== FUNCTIONAL EQUIVALENCE TEST ===")
# Safe execution of the two known controlled test snippets in isolated namespaces
scope_orig = {}
exec(example_code, scope_orig)
fn_orig = scope_orig["compute_stats"]

scope_trans = {}
exec(transformed_code, scope_trans)
fn_trans = scope_trans["compute_stats"]

test_inputs = [
    ([1.0, 2.0, 3.0, 4.0], 2.0),
    ([10.0, -5.0, 0.0], 0.5),
    ([], 1.0),
    ([100.0], 1.5)
]

all_match = True
for vals, scale in test_inputs:
    res_orig = fn_orig(vals, scale)
    res_trans = fn_trans(vals, scale)
    match = (res_orig == res_trans)
    print(f"Input: (values={vals}, scale={scale}) -> Orig: {res_orig} | Trans: {res_trans} | Match: {match}")
    if not match:
        all_match = False

print(f"\nALL TEST INPUTS PRODUCE IDENTICAL RESULTS: {all_match}")
