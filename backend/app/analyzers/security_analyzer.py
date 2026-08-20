"""Static security pattern analyzer for Python ASTs (zero-execution static detection)."""

import ast
import re
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    FindingCategory,
    FindingLocation,
    FindingSeverity,
    StructuralMetrics,
    SupportedLanguage,
)

# Common regex patterns for hardcoded credentials / tokens in strings
SECRET_KEY_PATTERN = re.compile(
    r"(?i)(api[_-]?key|auth[_-]?token|secret[_-]?key|password|access[_-]?token|private[_-]?key)\s*=\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]"
)
SQL_KEYWORD_PATTERN = re.compile(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|UNION)\b")


class SecurityPatternVisitor(ast.NodeVisitor):
    """Inspects AST nodes for insecure APIs, dynamic evaluation, and dangerous patterns."""

    def __init__(self):
        self.findings: List[AnalysisFinding] = []

    def visit_Call(self, node: ast.Call):
        lineno = getattr(node, "lineno", 1)

        # 1. Dynamic Evaluation: eval() and exec()
        if isinstance(node.func, ast.Name):
            if node.func.id == "eval":
                self.findings.append(
                    AnalysisFinding(
                        id="SEC-EVAL-01",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        title="Dynamic code execution via eval()",
                        description="Use of built-in eval() allows execution of arbitrary Python expressions at runtime.",
                        location=FindingLocation(line_start=lineno),
                        evidence="eval(...)",
                        recommendation="Use ast.literal_eval() for safe evaluation of literals or design a structured parser.",
                    )
                )
            elif node.func.id == "exec":
                self.findings.append(
                    AnalysisFinding(
                        id="SEC-EXEC-01",
                        category=FindingCategory.SECURITY,
                        severity=FindingSeverity.CRITICAL,
                        title="Dynamic code execution via exec()",
                        description="Use of built-in exec() allows execution of arbitrary Python code statements at runtime.",
                        location=FindingLocation(line_start=lineno),
                        evidence="exec(...)",
                        recommendation="Avoid executing dynamic code strings; use explicit dispatch dictionaries or functions.",
                    )
                )

        # 2. Subprocess & Shell Invocations
        elif isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if isinstance(node.func.value, ast.Name):
                val_id = node.func.value.id
                if val_id == "os" and attr in ("system", "popen", "spawnlp"):
                    self.findings.append(
                        AnalysisFinding(
                            id="SEC-SUBPROCESS-OS-01",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            title=f"Unsafe OS shell execution via os.{attr}()",
                            description=f"Invocation of os.{attr}() can expose system to command injection if arguments are untrusted.",
                            location=FindingLocation(line_start=lineno),
                            evidence=f"os.{attr}(...)",
                            recommendation="Use subprocess.run() with shell=False and argument arrays instead of shell strings.",
                        )
                    )
                elif val_id == "subprocess" and attr in ("run", "Popen", "call", "check_call", "check_output"):
                    # Check for shell=True
                    has_shell_true = any(
                        kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                        for kw in node.keywords
                    )
                    if has_shell_true:
                        self.findings.append(
                            AnalysisFinding(
                                id="SEC-SUBPROCESS-SHELL-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.HIGH,
                                title=f"subprocess.{attr}() executed with shell=True",
                                description="Passing shell=True to subprocess invocations is prone to shell injection attacks.",
                                location=FindingLocation(line_start=lineno),
                                evidence=f"subprocess.{attr}(..., shell=True)",
                                recommendation="Set shell=False and pass arguments as an explicit list of tokens.",
                            )
                        )
                    else:
                        self.findings.append(
                            AnalysisFinding(
                                id="SEC-SUBPROCESS-USAGE-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.LOW,
                                title=f"Subprocess invocation via subprocess.{attr}()",
                                description=f"External process execution via subprocess.{attr}(). Ensure all input arguments are sanitized.",
                                location=FindingLocation(line_start=lineno),
                                evidence=f"subprocess.{attr}(...)",
                                recommendation="Validate and constrain all executable paths and argument inputs.",
                            )
                        )

                # 3. Weak Cryptographic Hashing
                elif val_id == "hashlib" and attr.lower() in ("md5", "sha1"):
                    self.findings.append(
                        AnalysisFinding(
                            id="SEC-WEAK-CRYPTO-01",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.MEDIUM,
                            title=f"Weak cryptographic hash algorithm hashlib.{attr}()",
                            description=f"Algorithm hashlib.{attr}() is cryptographically broken and susceptible to collision attacks.",
                            location=FindingLocation(line_start=lineno),
                            evidence=f"hashlib.{attr}()",
                            recommendation="Use modern secure hashing algorithms like hashlib.sha256() or hashlib.sha3_256().",
                        )
                    )

                # 4. Insecure Deserialization (Pickle / Yaml)
                elif val_id == "pickle" and attr in ("loads", "load"):
                    self.findings.append(
                        AnalysisFinding(
                            id="SEC-DESERIAL-PICKLE-01",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            title=f"Insecure deserialization via pickle.{attr}()",
                            description="Unpickling untrusted data can lead to arbitrary remote code execution via object reconstruction.",
                            location=FindingLocation(line_start=lineno),
                            evidence=f"pickle.{attr}(...)",
                            recommendation="Use safe serialization formats like JSON, Protobuf, or msgpack for untrusted data.",
                        )
                    )
                elif val_id in ("yaml", "ruamel_yaml") and attr == "load":
                    has_safe_loader = any(
                        kw.arg == "Loader" and "Safe" in getattr(kw.value, "id", "")
                        for kw in node.keywords
                    )
                    if not has_safe_loader:
                        self.findings.append(
                            AnalysisFinding(
                                id="SEC-DESERIAL-YAML-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.MEDIUM,
                                title="Unsafe YAML deserialization via yaml.load()",
                                description="Calling yaml.load() without SafeLoader can instantiate arbitrary Python objects.",
                                location=FindingLocation(line_start=lineno),
                                evidence="yaml.load(...)",
                                recommendation="Use yaml.safe_load() or specify Loader=yaml.SafeLoader.",
                            )
                        )

                # 5. SQL String Concatenation Detection
                elif attr in ("execute", "executemany") and node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
                        # Detect string concatenation in query
                        self.findings.append(
                            AnalysisFinding(
                                id="SEC-SQL-CONCAT-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.HIGH,
                                title="Potential SQL injection via string concatenation",
                                description="SQL query is constructed using string concatenation (+) rather than parameterized bindings.",
                                location=FindingLocation(line_start=lineno),
                                evidence=f".{attr}(query + ...)",
                                recommendation="Use parameterized SQL queries (e.g. cursor.execute('SELECT ... WHERE id = %s', (id,)))",
                            )
                        )
                    elif isinstance(first_arg, ast.JoinedStr):
                        # f-string in query
                        self.findings.append(
                            AnalysisFinding(
                                id="SEC-SQL-FSTRING-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.HIGH,
                                title="Potential SQL injection via formatted f-string",
                                description="SQL query is constructed using f-string interpolation rather than parameterized placeholders.",
                                location=FindingLocation(line_start=lineno),
                                evidence=f".{attr}(f'SELECT ...')",
                                recommendation="Use parameterized SQL placeholders instead of inline string interpolation.",
                            )
                        )

        self.generic_visit(node)


class SecurityPatternAnalyzer(BaseAnalyzer):
    """Inspects code for common static security vulnerabilities without executing source code."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-SEC-01"

    @property
    def name(self) -> str:
        return "Static Security Vulnerability Analyzer"

    @property
    def description(self) -> str:
        return "Detects dynamic execution (eval/exec), unsafe subprocesses, SQL concatenation, weak crypto, and hardcoded secrets."

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [SupportedLanguage.PYTHON]

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: StructuralMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []

        if not code.strip():
            return findings

        # 1. AST-Based Security Pattern Scanner
        if ast_tree is not None:
            visitor = SecurityPatternVisitor()
            visitor.visit(ast_tree)
            findings.extend(visitor.findings)

        # 2. Hardcoded Secrets Static Pattern Scan
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            match = SECRET_KEY_PATTERN.search(line)
            if match:
                # Exclude dummy test values
                matched_str = match.group(0)
                if not any(dummy in matched_str.lower() for dummy in ("placeholder", "example", "dummy", "test")):
                    findings.append(
                        AnalysisFinding(
                            id="SEC-SECRET-HARDCODED-01",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.HIGH,
                            title="Potential hardcoded secret or API credential",
                            description="Static pattern matched potential hardcoded API key, token, or password assignment.",
                            location=FindingLocation(line_start=idx),
                            evidence=f"Line {idx}: {matched_str[:40]}...",
                            recommendation="Store secrets in environment variables or external secrets managers (e.g. os.environ).",
                        )
                    )

        return findings
