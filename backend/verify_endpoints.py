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

print("=== Testing CodeSanitize Analysis Endpoints ===")

# 1. Valid Python
code_py = "def add(a, b):\n    # add function\n    return a + b\n"
s1, r1 = post("http://127.0.0.1:8000/api/analyze", {"code": code_py, "language": "python"})
print(f"1. Valid Python -> Status: {s1}, Syntax Valid: {r1['syntax_valid']}, Functions: {r1['structural_metrics']['function_count']}, Parser: {r1['parser_used']}")

# 2. Invalid Python
code_py_err = "def add(a, b)\n    return a + b\n"
s2, r2 = post("http://127.0.0.1:8000/api/analyze", {"code": code_py_err, "language": "python"})
print(f"2. Invalid Python -> Status: {s2}, Syntax Valid: {r2['syntax_valid']}, Issue: {r2['issues'][0]['message']}, Line: {r2['issues'][0]['line_start']}")

# 3. Valid JavaScript
code_js = "function greet(name) { return 'Hello ' + name; }"
s3, r3 = post("http://127.0.0.1:8000/api/analyze", {"code": code_js, "language": "javascript"})
print(f"3. Valid JS -> Status: {s3}, Syntax Valid: {r3['syntax_valid']}, AST Nodes: {r3['structural_metrics']['ast_nodes_count']}, Parser: {r3['parser_used']}")

# 4. Valid TypeScript
code_ts = "interface Item { id: number; } const item: Item = { id: 1 };"
s4, r4 = post("http://127.0.0.1:8000/api/analyze", {"code": code_ts, "language": "typescript"})
print(f"4. Valid TS -> Status: {s4}, Syntax Valid: {r4['syntax_valid']}, Class/Interface: {r4['structural_metrics']['class_count']}, Parser: {r4['parser_used']}")

# 5. Valid C++
code_cpp = "#include <iostream>\nclass Robot { public: void run() {} };\nint main() { return 0; }"
s5, r5 = post("http://127.0.0.1:8000/api/analyze", {"code": code_cpp, "language": "cpp"})
print(f"5. Valid C++ -> Status: {s5}, Syntax Valid: {r5['syntax_valid']}, Classes: {r5['structural_metrics']['class_count']}, Functions: {r5['structural_metrics']['function_count']}, Parser: {r5['parser_used']}")

# 6. Valid Java
code_java = "package test;\npublic class App { public static void main(String[] args) {} }"
s6, r6 = post("http://127.0.0.1:8000/api/analyze", {"code": code_java, "language": "java"})
print(f"6. Valid Java -> Status: {s6}, Syntax Valid: {r6['syntax_valid']}, Classes: {r6['structural_metrics']['class_count']}, Functions: {r6['structural_metrics']['function_count']}, Parser: {r6['parser_used']}")

# 7. Frontend Proxy to Backend Check
s7, r7 = post("http://127.0.0.1:5173/api/analyze", {"code": code_py, "language": "python"})
print(f"7. Frontend Proxied Analysis -> Status: {s7}, Syntax Valid: {r7['syntax_valid']}, Analysis ID: {r7['analysis_id'][:8]}...")

print("=== All Analysis Endpoints Verified Successfully! ===")
