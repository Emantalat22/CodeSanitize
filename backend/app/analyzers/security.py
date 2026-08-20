"""Security Static Pattern Analyzer for dangerous calls, secrets, weak crypto, and SQL injection risks across languages."""

import ast
import re
from typing import Any, Dict, List, Optional
from app.analyzers.base import BaseAnalyzer
from app.models.schemas import (
    AnalysisFinding,
    CodeMetrics,
    FindingCategory,
    FindingLocation,
    FindingSeverity,
    SecurityReport,
    SupportedLanguage,
)


class SecurityAnalyzer(BaseAnalyzer):
    """Static pattern analyzer detecting security antipatterns and risk vectors without executing code."""

    @property
    def analyzer_id(self) -> str:
        return "ANLZ-SEC-01"

    @property
    def name(self) -> str:
        return "Static Security Vulnerability Analyzer"

    @property
    def description(self) -> str:
        return (
            "Detects dangerous functions (eval, exec), insecure subprocess invocation, "
            "hardcoded secrets, weak cryptographic hashes, and SQL string concatenation risks."
        )

    @property
    def supported_languages(self) -> List[SupportedLanguage]:
        return [
            SupportedLanguage.PYTHON,
            SupportedLanguage.JAVASCRIPT,
            SupportedLanguage.TYPESCRIPT,
            SupportedLanguage.JAVA,
            SupportedLanguage.CPP,
            SupportedLanguage.C,
            SupportedLanguage.GO,
            SupportedLanguage.RUST,
            SupportedLanguage.PHP,
            SupportedLanguage.RUBY,
            SupportedLanguage.CSHARP,
        ]

    def analyze(
        self,
        code: str,
        ast_tree: Optional[ast.AST],
        metrics: CodeMetrics,
        options: Dict[str, Any],
    ) -> List[AnalysisFinding]:
        """Perform purely static pattern inspection."""
        findings: List[AnalysisFinding] = []

        if ast_tree is not None and isinstance(ast_tree, ast.AST):
            findings.extend(self._inspect_ast_security(ast_tree))
        else:
            findings.extend(self._inspect_generic_text_vulnerabilities(code))

        # Hardcoded secrets regex inspects all languages
        findings.extend(self._inspect_secrets(code))

        return findings

    def _inspect_ast_security(self, tree: ast.AST) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []

        for node in ast.walk(tree):
            # 1. Dynamic Code Execution: eval() & exec()
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name == "eval":
                    findings.append(
                        AnalysisFinding(
                            id="SEC-EVAL-01",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.CRITICAL,
                            title="Dynamic code execution via eval()",
                            description="Use of eval() introduces arbitrary remote code execution vulnerabilities.",
                            location=FindingLocation(line_start=node.lineno),
                            evidence="eval(...)",
                            recommendation="Use ast.literal_eval() for safe evaluation of literals or design a structured parser.",
                        )
                    )
                elif func_name == "exec":
                    findings.append(
                        AnalysisFinding(
                            id="SEC-EXEC-01",
                            category=FindingCategory.SECURITY,
                            severity=FindingSeverity.CRITICAL,
                            title="Dynamic statement execution via exec()",
                            description="Use of exec() executes arbitrary Python source code at runtime.",
                            location=FindingLocation(line_start=node.lineno),
                            evidence="exec(...)",
                            recommendation="Refactor dynamic execution into statically typed dispatch patterns.",
                        )
                    )

                # 2. Insecure Subprocess Execution with shell=True
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    module_name = node.func.value.id
                    method_name = node.func.attr

                    if module_name in ("subprocess", "os") and method_name in (
                        "run",
                        "Popen",
                        "call",
                        "check_call",
                        "check_output",
                        "system",
                        "popen",
                    ):
                        is_shell_true = False
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                is_shell_true = True

                        if is_shell_true or method_name in ("system", "popen"):
                            findings.append(
                                AnalysisFinding(
                                    id="SEC-SUBPROCESS-SHELL-01",
                                    category=FindingCategory.SECURITY,
                                    severity=FindingSeverity.HIGH,
                                    title=f"Command injection risk via {module_name}.{method_name}() with shell=True",
                                    description="Executing subprocess commands with shell=True enables command injection if input is untrusted.",
                                    location=FindingLocation(line_start=node.lineno),
                                    evidence=f"{module_name}.{method_name}(..., shell=True)",
                                    recommendation="Pass command arguments as a list of strings [cmd, arg1, arg2] and set shell=False.",
                                )
                            )

                # 3. Weak Cryptographic Hash: hashlib.md5 / hashlib.sha1
                if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "hashlib" and node.func.attr in ("md5", "sha1"):
                        findings.append(
                            AnalysisFinding(
                                id="SEC-WEAK-CRYPTO-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.MEDIUM,
                                title=f"Weak cryptographic hash algorithm hashlib.{node.func.attr}()",
                                description=f"Algorithm '{node.func.attr}' is cryptographically broken and vulnerable to collision attacks.",
                                location=FindingLocation(line_start=node.lineno),
                                evidence=f"hashlib.{node.func.attr}()",
                                recommendation="Use SHA-256 (hashlib.sha256()) or modern password hashing (argon2, bcrypt).",
                            )
                        )

            # 4. Insecure / Dangerous Imports
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imported_modules: List[str] = []
                if isinstance(node, ast.Import):
                    imported_modules = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_modules = [node.module]

                for mod in imported_modules:
                    if mod in ("telnetlib", "pickle", "cPickle", "shelve"):
                        findings.append(
                            AnalysisFinding(
                                id="SEC-DANGEROUS-IMPORT-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.MEDIUM,
                                title=f"Potentially unsafe module import: '{mod}'",
                                description=f"Module '{mod}' has known security implications (e.g. unauthenticated cleartext or arbitrary deserialization).",
                                location=FindingLocation(line_start=node.lineno),
                                evidence=f"import {mod}",
                                recommendation="Consider using modern encrypted alternatives (e.g. json, cryptography, paramiko).",
                            )
                        )

            # 5. Suspicious SQL Query String Concatenation
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    val_upper = node.left.value.upper()
                    if any(sql in val_upper for sql in ("SELECT ", "INSERT INTO ", "UPDATE ", "DELETE FROM ", "DROP ")):
                        findings.append(
                            AnalysisFinding(
                                id="SEC-SQL-CONCAT-01",
                                category=FindingCategory.SECURITY,
                                severity=FindingSeverity.HIGH,
                                title="Potential SQL Injection via string concatenation",
                                description="SQL query string is assembled using direct concatenation rather than parameterized query bindings.",
                                location=FindingLocation(line_start=node.lineno),
                                evidence=node.left.value[:40] + " + ...",
                                recommendation="Use parameterized SQL placeholders (e.g. db.execute('SELECT * FROM users WHERE id = %s', (id,)))",
                            )
                        )

        return findings

    def _inspect_secrets(self, code: str) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []
        lines = code.splitlines()

        secret_patterns = [
            (
                r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|private[_-]?key)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
                "SEC-SECRET-HARDCODED-01",
                "Potential hardcoded secret or API credential",
                FindingSeverity.HIGH,
            ),
            (
                r"(?i)password\s*[:=]\s*['\"][^'\"]{4,}['\"]",
                "SEC-PASSWORD-HARDCODED-01",
                "Potential hardcoded plaintext password",
                FindingSeverity.MEDIUM,
            ),
        ]

        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith(("#", "//", "/*", "*")):
                continue

            for pattern, rule_id, title, severity in secret_patterns:
                if re.search(pattern, line):
                    findings.append(
                        AnalysisFinding(
                            id=rule_id,
                            category=FindingCategory.SECURITY,
                            severity=severity,
                            title=title,
                            description="Credentials should never be committed into source code or hardcoded.",
                            location=FindingLocation(line_start=line_idx),
                            evidence=line.strip()[:60],
                            recommendation="Load secrets from environment variables or secure secret managers.",
                        )
                    )

        return findings

    def _inspect_generic_text_vulnerabilities(self, code: str) -> List[AnalysisFinding]:
        findings: List[AnalysisFinding] = []
        lines = code.splitlines()

        generic_vulnerabilities = [
            (
                r"\beval\s*\(",
                "SEC-EVAL-01",
                "Dynamic code execution via eval()",
                FindingSeverity.CRITICAL,
            ),
            (
                r"\bexec\s*\(",
                "SEC-EXEC-01",
                "Dynamic execution via exec()",
                FindingSeverity.CRITICAL,
            ),
            (
                r"\b(Runtime\.getRuntime\(\)\.exec|system\s*\(|popen\s*\()",
                "SEC-CMD-INJECTION-01",
                "Command execution function invoked",
                FindingSeverity.HIGH,
            ),
        ]

        for line_idx, line in enumerate(lines, start=1):
            trimmed = line.strip()
            if trimmed.startswith(("#", "//", "/*", "*")):
                continue

            for pattern, rule_id, title, severity in generic_vulnerabilities:
                if re.search(pattern, line):
                    findings.append(
                        AnalysisFinding(
                            id=rule_id,
                            category=FindingCategory.SECURITY,
                            severity=severity,
                            title=title,
                            description=f"Potential vulnerability pattern detected on line {line_idx}.",
                            location=FindingLocation(line_start=line_idx),
                            evidence=line.strip()[:60],
                            recommendation="Review dynamic calls and ensure inputs are strictly validated.",
                        )
                    )

        return findings

    @classmethod
    def generate_report(cls, findings: List[AnalysisFinding]) -> SecurityReport:
        """Aggregate security findings into a structured SecurityReport."""
        sec_findings = [f for f in findings if f.category == FindingCategory.SECURITY]

        crit_count = sum(1 for f in sec_findings if f.severity == FindingSeverity.CRITICAL)
        warn_count = sum(
            1 for f in sec_findings if f.severity in (FindingSeverity.HIGH, FindingSeverity.MEDIUM)
        )
        info_count = sum(
            1 for f in sec_findings if f.severity in (FindingSeverity.LOW, FindingSeverity.INFO)
        )

        if crit_count > 0:
            risk_level = "Critical"
        elif warn_count > 2:
            risk_level = "High"
        elif warn_count > 0:
            risk_level = "Medium"
        elif info_count > 0:
            risk_level = "Low"
        else:
            risk_level = "Clean"

        return SecurityReport(
            critical_count=crit_count,
            warning_count=warn_count,
            informational_count=info_count,
            risk_level=risk_level,
            findings=sec_findings,
        )
