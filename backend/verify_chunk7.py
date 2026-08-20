"""End-to-End Verification script for Chunk 7 Production Hardening & Developer Platform."""

import io
import json
import urllib.request
import zipfile

BASE_URL = "http://127.0.0.1:8000"


def post_json(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def get_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def get_text(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), resp.read().decode("utf-8")


def main():
    print("=== Chunk 7 Production Hardening & Developer Platform Verification ===\n")

    # 1. Multi-File Project Analysis & Duplication Detection
    calc_py = '''def calculate_total(prices, tax_rate):
    subtotal = sum(prices)
    tax = subtotal * tax_rate
    return subtotal + tax
'''
    invoice_py = '''def calculate_total_clone(prices, tax_rate):
    subtotal = sum(prices)
    tax = subtotal * tax_rate
    return subtotal + tax
'''
    client_ts = '''export interface Customer {
    id: string;
    name: string;
}

export function formatCustomer(c: Customer): string {
    return `Customer: ${c.name} (#${c.id})`;
}
'''
    server_go = '''package main

import "fmt"

func ProcessBatch(items []string) int {
    if len(items) == 0 {
        return 0
    }
    fmt.Println("Processing items count:", len(items))
    return len(items)
}
'''

    project_payload = {
        "project_name": "ECommerceCore",
        "files": [
            {"filename": "src/calc.py", "code": calc_py, "language": "python"},
            {"filename": "src/invoice.py", "code": invoice_py, "language": "python"},
            {"filename": "src/client.ts", "code": client_ts, "language": "typescript"},
            {"filename": "src/server.go", "code": server_go, "language": "go"},
        ],
    }

    code, res_proj = post_json(f"{BASE_URL}/api/project/analyze", project_payload)
    print(f"1. POST /api/project/analyze -> Status: {code}")
    print(f"   Project: {res_proj['project_name']} (ID: {res_proj['project_id'][:8]}...)")
    print(f"   Total Files: {res_proj['total_files']}, Total LOC: {res_proj['total_lines_of_code']}")
    print(f"   Overall Quality Score: {res_proj['overall_quality_score']}/100")
    print(f"   Language Distribution: {res_proj['language_distribution']}")
    print(f"   Duplications Detected: {len(res_proj['duplications'])}")
    for d in res_proj["duplications"]:
        print(f"   - [{d['similarity_percentage']}%] {d['duplicate_type']}: {d['primary_location']['filename']} -> {d['duplicate_location']['filename']}")
    print(f"   Recommendations ({len(res_proj['recommendations'])}): {res_proj['recommendations'][:2]}")

    # 2. Test HTML & JSON Report Export for this project
    scan_id = res_proj["project_id"]
    code_html, report_html = get_text(f"{BASE_URL}/api/reports/{scan_id}/html")
    print(f"\n2. GET /api/reports/{scan_id}/html -> Status: {code_html}, Length: {len(report_html)} bytes")
    assert "<!DOCTYPE html>" in report_html
    assert "ECommerceCore" in report_html

    # 3. Test Local History Persistence
    code_hist, history_list = get_json(f"{BASE_URL}/api/history")
    print(f"\n3. GET /api/history -> Status: {code_hist}, Scans Count: {len(history_list)}")
    matching = [h for h in history_list if h["scan_id"] == scan_id]
    print(f"   Found Project Scan in History: {len(matching) > 0}, Target: {matching[0]['target_name'] if matching else 'None'}")

    # 4. Backward Compatibility Check (Single File Analyze, Transform, Validate)
    code_single, res_single = post_json(
        f"{BASE_URL}/api/analyze",
        {"code": "def ping(): return 'pong'\n", "language": "python", "filename": "ping.py"},
    )
    print(f"\n4. Single File POST /api/analyze -> Status: {code_single}, Score: {res_single['quality_score']}/100")

    code_trans, res_trans = post_json(
        f"{BASE_URL}/api/transform",
        {"code": "def sample(a):\n    temp = a * 2\n    return temp\n", "language": "python"},
    )
    print(f"   POST /api/transform -> Status: {code_trans}, Status: {res_trans['transformation_status']}, Verdict: {res_trans['validation_status']}")

    print("\n=== Chunk 7 Verification Completed Successfully! ===")


if __name__ == "__main__":
    main()
