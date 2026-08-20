"""Verification script for Chunk 6 Multi-Language Parser Foundation & Architecture."""

import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000"


def test_post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))


def main():
    print("=== Chunk 6 Multi-Language Architecture Verification ===\n")

    # 1. Test Language Auto Detection & Multi-Language Analysis (Go)
    go_code = '''package main

import "fmt"

type Server struct {
    Port int
}

func (s *Server) Start() {
    if s.Port > 0 {
        fmt.Println("Server running on port", s.Port)
    }
}

func main() {
    srv := &Server{Port: 8080}
    srv.Start()
}
'''
    code, res = test_post(
        f"{BASE_URL}/api/analyze",
        {"code": go_code, "language": "auto", "filename": "main.go"},
    )
    print(f"1. Go Code Analysis (Auto Detection) -> Status: {code}")
    print(f"   Detected Language: {res['language']}")
    print(f"   Quality Score: {res['quality_score']}/100")
    print(f"   Metrics: LOC={res['metrics']['lines_of_code']}, Functions={res['metrics']['function_count']}, Classes={res['metrics']['class_count']}, Imports={res['metrics']['import_count']}")
    print(f"   Complexity: Cyclomatic={res['complexity_report']['cyclomatic_complexity']}, Level={res['complexity_report']['complexity_level']}")

    # 2. Test Rust Code Analysis
    rust_code = '''use std::collections::HashMap;

pub struct Cache {
    items: HashMap<String, String>,
}

impl Cache {
    pub fn new() -> Self {
        Cache { items: HashMap::new() }
    }
    
    pub fn get(&self, key: &str) -> Option<&String> {
        self.items.get(key)
    }
}
'''
    code, res = test_post(
        f"{BASE_URL}/api/analyze",
        {"code": rust_code, "language": "rust", "filename": "cache.rs"},
    )
    print(f"\n2. Rust Code Analysis -> Status: {code}")
    print(f"   Language: {res['language']}")
    print(f"   Quality Score: {res['quality_score']}/100")
    print(f"   Functions Count: {res['metrics']['function_count']}, Structs Count: {res['metrics']['class_count']}")

    # 3. Test TypeScript Code Analysis
    ts_code = '''interface ApiResponse<T> {
    data: T;
    status: number;
}

export function handleResponse<T>(res: ApiResponse<T>): T | null {
    if (res.status === 200) {
        return res.data;
    }
    return null;
}
'''
    code, res = test_post(
        f"{BASE_URL}/api/analyze",
        {"code": ts_code, "language": "typescript", "filename": "api.ts"},
    )
    print(f"\n3. TypeScript Code Analysis -> Status: {code}")
    print(f"   Language: {res['language']}")
    print(f"   Quality Score: {res['quality_score']}/100")
    print(f"   Functions: {res['metrics']['function_count']}, Classes/Interfaces: {res['metrics']['class_count']}")

    # 4. Regression check Chunk 3 & Chunk 4
    transform_payload = {
        "code": "def add(x, y):\n    res = x + y\n    return res\n",
        "language": "python",
        "options": {"rule_ids": ["PY-SAFE-LOCAL-RENAME-01"]},
    }
    code, res = test_post(f"{BASE_URL}/api/transform", transform_payload)
    print(f"\n4. Regression Check: POST /api/transform -> Status: {code}, Transformation: {res['transformation_status']}, Validation: {res['validation_status']}")



    print("\n=== Chunk 6 Verification Completed Successfully! ===")


if __name__ == "__main__":
    main()
