"""Comprehensive tests for Chunk 6 Multi-Language Parser Foundation & Architecture."""

import ast
import pytest
from fastapi.testclient import TestClient
from app.models.cir import IRProgram

from app.models.schemas import SupportedLanguage
from app.parsers.cir_extractor import CIRExtractor
from app.parsers.language_detector import LanguageDetector
from app.parsers.registry import ParserRegistry


# ===================================================
# 1. Automatic Language Detection Tests
# ===================================================

def test_language_detector_by_filename_extension():
    """Verify language detection across various filename extensions."""
    assert LanguageDetector.detect("", "main.py") == SupportedLanguage.PYTHON
    assert LanguageDetector.detect("", "index.js") == SupportedLanguage.JAVASCRIPT
    assert LanguageDetector.detect("", "app.ts") == SupportedLanguage.TYPESCRIPT
    assert LanguageDetector.detect("", "Application.java") == SupportedLanguage.JAVA
    assert LanguageDetector.detect("", "engine.cpp") == SupportedLanguage.CPP
    assert LanguageDetector.detect("", "driver.c") == SupportedLanguage.C
    assert LanguageDetector.detect("", "server.go") == SupportedLanguage.GO
    assert LanguageDetector.detect("", "lib.rs") == SupportedLanguage.RUST
    assert LanguageDetector.detect("", "script.rb") == SupportedLanguage.RUBY
    assert LanguageDetector.detect("", "index.php") == SupportedLanguage.PHP
    assert LanguageDetector.detect("", "Program.cs") == SupportedLanguage.CSHARP


def test_language_detector_by_shebang():
    """Verify language detection from #! header lines."""
    py_code = "#!/usr/bin/env python3\nprint('hello')\n"
    js_code = "#!/usr/bin/env node\nconsole.log('hello');\n"
    rb_code = "#!/usr/bin/env ruby\nputs 'hello'\n"

    assert LanguageDetector.detect(py_code) == SupportedLanguage.PYTHON
    assert LanguageDetector.detect(js_code) == SupportedLanguage.JAVASCRIPT
    assert LanguageDetector.detect(rb_code) == SupportedLanguage.RUBY


def test_language_detector_by_syntax_heuristics():
    """Verify language detection by token and keyword analysis."""
    go_code = '''package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
'''
    assert LanguageDetector.detect(go_code) == SupportedLanguage.GO

    rust_code = '''fn main() {
    let mut x = 42;
    println!("Value: {}", x);
}
'''
    assert LanguageDetector.detect(rust_code) == SupportedLanguage.RUST

    java_code = '''package com.example;

public class Greeter {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
'''
    assert LanguageDetector.detect(java_code) == SupportedLanguage.JAVA

    cpp_code = '''#include <iostream>

int main() {
    std::cout << "Hello C++" << std::endl;
    return 0;
}
'''
    assert LanguageDetector.detect(cpp_code) == SupportedLanguage.CPP

    php_code = '''<?php
function greet($name) {
    echo "Hello " . $name;
}
'''
    assert LanguageDetector.detect(php_code) == SupportedLanguage.PHP


# ===================================================
# 2. Parser Registry & Multi-Language Dispatch Tests
# ===================================================

def test_parser_registry_initialization():
    """Verify all required languages have registered parsers."""
    required = [
        SupportedLanguage.PYTHON,
        SupportedLanguage.JAVASCRIPT,
        SupportedLanguage.TYPESCRIPT,
        SupportedLanguage.JAVA,
        SupportedLanguage.CPP,
        SupportedLanguage.C,
        SupportedLanguage.GO,
        SupportedLanguage.RUST,
    ]
    for lang in required:
        assert ParserRegistry.is_language_supported(lang) is True
        parser = ParserRegistry.get_parser(lang)
        assert parser is not None
        assert parser.is_available() is True


def test_parser_registry_get_language_infos():
    """Verify language infos list all target languages with availability metadata."""
    infos = ParserRegistry.get_language_infos()
    assert len(infos) >= 8
    lang_ids = [info.id for info in infos]
    assert SupportedLanguage.PYTHON in lang_ids
    assert SupportedLanguage.GO in lang_ids
    assert SupportedLanguage.RUST in lang_ids


# ===================================================
# 3. Common Intermediate Representation (CIR) Extraction
# ===================================================

def test_cir_extractor_python():
    """Verify CIR extraction from Python source code."""
    code = '''import os

class Model:
    def evaluate(self, x: int) -> int:
        if x > 0:
            return x * 2
        return 0
'''
    tree = ast.parse(code)
    cir = CIRExtractor.extract(code, SupportedLanguage.PYTHON, tree)
    assert isinstance(cir, IRProgram)
    assert cir.lines_of_code > 5
    assert len(cir.classes) == 1
    assert len(cir.functions) == 1
    assert len(cir.imports) == 1
    assert len(cir.control_flows) >= 1
    assert cir.total_cyclomatic_complexity >= 2



def test_cir_extractor_go():
    """Verify CIR extraction from Go source code."""
    code = '''package main

import "fmt"

type Worker struct {
    ID int
}

func ProcessItem(item string) bool {
    if len(item) > 0 {
        fmt.Println(item)
        return true
    }
    return false
}
'''
    cir = CIRExtractor.extract(code, SupportedLanguage.GO, None)
    assert isinstance(cir, IRProgram)
    assert cir.lines_of_code > 10
    assert len(cir.functions) >= 1
    assert len(cir.classes) >= 1
    assert len(cir.imports) >= 1
    assert len(cir.control_flows) >= 1


def test_cir_extractor_rust():
    """Verify CIR extraction from Rust source code."""
    code = '''use std::collections::HashMap;

pub struct Config {
    pub port: u16,
}

fn handle_request(req_id: u32) -> bool {
    if req_id > 0 {
        return true;
    }
    false
}
'''
    cir = CIRExtractor.extract(code, SupportedLanguage.RUST, None)
    assert isinstance(cir, IRProgram)
    assert cir.lines_of_code > 8
    assert len(cir.functions) >= 1
    assert len(cir.classes) >= 1
    assert len(cir.imports) >= 1


# ===================================================
# 4. Multi-Language POST /api/analyze Integration Tests
# ===================================================

def test_api_analyze_go_code(client: TestClient):
    """Verify POST /api/analyze successfully parses and analyzes Go code."""
    go_code = '''package main

import "fmt"

func CalculateSum(a int, b int) int {
    if a > 0 {
        return a + b
    }
    return b
}
'''
    res = client.post(
        "/api/analyze",
        json={"code": go_code, "language": "go", "filename": "calc.go"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["language"] == "go"
    assert data["metrics"]["lines_of_code"] > 5
    assert data["metrics"]["function_count"] >= 1
    assert data["metrics"]["import_count"] >= 1
    assert data["quality_score"] > 80


def test_api_analyze_rust_code(client: TestClient):
    """Verify POST /api/analyze successfully parses and analyzes Rust code."""
    rust_code = '''fn compute(val: i32) -> i32 {
    if val > 10 {
        val * 2
    } else {
        val
    }
}
'''
    res = client.post(
        "/api/analyze",
        json={"code": rust_code, "language": "rust", "filename": "compute.rs"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["language"] == "rust"
    assert data["metrics"]["function_count"] >= 1
    assert data["quality_score"] > 80


def test_api_analyze_javascript_code(client: TestClient):
    """Verify POST /api/analyze successfully parses and analyzes JavaScript code."""
    js_code = '''function formatName(first, last) {
    if (!first) return last;
    return `${first} ${last}`;
}
'''
    res = client.post(
        "/api/analyze",
        json={"code": js_code, "language": "javascript", "filename": "utils.js"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["language"] == "javascript"
    assert data["metrics"]["function_count"] >= 1


def test_api_analyze_typescript_code(client: TestClient):
    """Verify POST /api/analyze successfully parses and analyzes TypeScript code."""
    ts_code = '''interface User {
    id: number;
    name: string;
}

function getUserName(user: User): string {
    return user.name;
}
'''
    res = client.post(
        "/api/analyze",
        json={"code": ts_code, "language": "typescript", "filename": "user.ts"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["language"] == "typescript"
    assert data["metrics"]["class_count"] >= 1
    assert data["metrics"]["function_count"] >= 1


def test_api_analyze_java_code(client: TestClient):
    """Verify POST /api/analyze successfully parses and analyzes Java code."""
    java_code = '''package com.app;

public class MathHelper {
    public static int multiply(int a, int b) {
        if (a == 0 || b == 0) {
            return 0;
        }
        return a * b;
    }
}
'''
    res = client.post(
        "/api/analyze",
        json={"code": java_code, "language": "java", "filename": "MathHelper.java"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["language"] == "java"
    assert data["metrics"]["class_count"] >= 1
    assert data["metrics"]["function_count"] >= 1


def test_api_analyze_cpp_code(client: TestClient):
    """Verify POST /api/analyze successfully parses and analyzes C++ code."""
    cpp_code = '''#include <iostream>

class Engine {
public:
    void start() {
        std::cout << "Engine started" << std::endl;
    }
};
'''
    res = client.post(
        "/api/analyze",
        json={"code": cpp_code, "language": "cpp", "filename": "engine.cpp"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["syntax_valid"] is True
    assert data["language"] == "cpp"
    assert data["metrics"]["class_count"] >= 1
    assert data["metrics"]["import_count"] >= 1


def test_api_analyze_auto_language_detection(client: TestClient):
    """Verify POST /api/analyze automatically detects language when language='auto'."""
    go_code = '''package main

import "fmt"

func main() {
    fmt.Println("Auto Go")
}
'''
    res = client.post(
        "/api/analyze",
        json={"code": go_code, "language": "auto", "filename": "server.go"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "go"

