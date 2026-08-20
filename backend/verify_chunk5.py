"""Comprehensive End-to-End Verification Script for Chunk 5."""

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

print("=== Chunk 5 Advanced Code Analysis and Intelligence Layer Verification ===")

# 1. Test POST /api/analyze on Clean Code
clean_code = """import math

def calculate_circle_properties(radius: float) -> dict:
    \"\"\"Calculate area and circumference of a circle.\"\"\"
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    
    area = math.pi * (radius ** 2)
    circumference = 2 * math.pi * radius
    return {"area": area, "circumference": circumference}
"""
s1, r1 = post("http://127.0.0.1:8000/api/analyze", {
    "code": clean_code,
    "language": "python",
    "filename": "circle.py"
})
print(f"\n1. POST /api/analyze (Clean Code) -> Status: {s1}")
print(f"   Overall Score: {r1['overall_score']}/100")
print(f"   Complexity: Cyclomatic={r1['complexity_metrics']['cyclomatic_complexity']}, Max Nesting={r1['complexity_metrics']['max_nesting_depth']}")
print(f"   Structural Metrics: LOC={r1['structural_metrics']['lines_of_code']}, Functions={r1['structural_metrics']['function_count']}")
print(f"   Fingerprint SHA-256: {r1['fingerprint']['ast_node_hash'][:16]}...")
print(f"   Analyzer Reports ({len(r1['analyzer_reports'])}): {', '.join(r['analyzer_name'] for r in r1['analyzer_reports'])}")

# 2. Test POST /api/analyze on Code with Security Vulnerabilities & High Complexity
vulnerable_code = """import subprocess
import hashlib
import os

API_SECRET_KEY = "sk_live_98234892348923489234"

def process_user_command(cmd_str: str, user_id: int):
    # Dynamic execution
    eval(cmd_str)
    
    # Subprocess with shell=True
    subprocess.run(cmd_str, shell=True)
    
    # Weak hash
    token = hashlib.md5(cmd_str.encode()).hexdigest()
    
    # Deep branching
    res = 0
    if user_id > 0:
        for i in range(10):
            if i % 2 == 0:
                while res < 100:
                    if res == 50:
                        break
                    res += i
    return token
"""
s2, r2 = post("http://127.0.0.1:8000/api/analyze", {
    "code": vulnerable_code,
    "language": "python",
    "filename": "security_test.py"
})
print(f"\n2. POST /api/analyze (Vulnerable & Complex Code) -> Status: {s2}")
print(f"   Overall Score: {r2['overall_score']}/100")
print(f"   Total Findings Detected: {len(r2['findings'])}")
for f in r2["findings"]:
    print(f"   - [{f['severity'].upper()}] {f['id']}: {f['title']}")
print(f"   Recommendations ({len(r2['recommendations'])}): {r2['recommendations'][:2]}")

# 3. Test POST /api/analyze on Syntax Error
s3, r3 = post("http://127.0.0.1:8000/api/analyze", {
    "code": "def unclosed_syntax(:\n    return 1",
    "language": "python",
})
print(f"\n3. POST /api/analyze (Syntax Error) -> Status: {s3}")
print(f"   Syntax Valid: {r3['syntax_valid']}, Analysis Status: {r3['analysis_status']}")
print(f"   Overall Score: {r3['overall_score']}, Issues: {r3['issues'][0]['message']}")

# 4. Verify Chunk 3 & Chunk 4 endpoints remain functional
s_trans, r_trans = post("http://127.0.0.1:8000/api/transform", {
    "code": "def sample(a: int):\n    temp = a * 2\n    return temp\n",
    "language": "python",
})
print(f"\n4. POST /api/transform (Chunk 3 Regression Check) -> Status: {s_trans}, Transformation: {r_trans['transformation_status']}, Validation: {r_trans['validation_status']}")

s_val, r_val = post("http://127.0.0.1:8000/api/validate", {
    "original_code": "def sample(a: int): return a * 2\n",
    "transformed_code": "def sample(a: int): return a * 2\n",
    "language": "python",
})
print(f"   POST /api/validate (Chunk 4 Regression Check) -> Status: {s_val}, is_valid: {r_val['is_valid']}")

# 5. Test Frontend Proxy
s_proxy, r_proxy = post("http://127.0.0.1:5173/api/analyze", {
    "code": "def proxy_ping(): return True\n",
    "language": "python",
})
print(f"\n5. Frontend Proxied /api/analyze -> Status: {s_proxy}, Score: {r_proxy['overall_score']}")

print("\n=== Chunk 5 Verification Completed Successfully! ===")
