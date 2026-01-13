#!/usr/bin/env python3
"""
Code Review Tool for Restaurant Rating Normalization Project

Analyzes Python files for:
- Security issues (API key exposure, SQL injection, XSS, etc.)
- Performance problems (inefficient loops, memory leaks, etc.)
- Style violations (PEP 8, naming conventions, etc.)

Usage:
    python scripts/code_review.py [file_path]
    python scripts/code_review.py backend/naver_api.py
    python scripts/code_review.py  # Reviews all Python files
"""

import os
import re
import ast
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    CRITICAL = "🔴 Critical"
    SUGGESTION = "🟡 Suggestion"
    GOOD = "🟢 Good"


@dataclass
class Finding:
    severity: Severity
    category: str  # Security, Performance, Style
    message: str
    line_number: int = 0
    code_snippet: str = ""


@dataclass
class ReviewReport:
    file_path: str
    findings: List[Finding] = field(default_factory=list)

    def add_finding(self, severity: Severity, category: str, message: str,
                    line_number: int = 0, code_snippet: str = ""):
        self.findings.append(Finding(
            severity=severity,
            category=category,
            message=message,
            line_number=line_number,
            code_snippet=code_snippet
        ))

    def print_report(self):
        print(f"\n{'='*80}")
        print(f"📄 File: {self.file_path}")
        print(f"{'='*80}\n")

        if not self.findings:
            print("✅ No issues found!\n")
            return

        # Group by severity
        by_severity = {
            Severity.CRITICAL: [],
            Severity.SUGGESTION: [],
            Severity.GOOD: []
        }

        for finding in self.findings:
            by_severity[finding.severity].append(finding)

        # Print in order: Critical -> Suggestion -> Good
        for severity in [Severity.CRITICAL, Severity.SUGGESTION, Severity.GOOD]:
            items = by_severity[severity]
            if not items:
                continue

            print(f"\n{severity.value} ({len(items)} items)")
            print("-" * 80)

            for finding in items:
                print(f"\n[{finding.category}]")
                if finding.line_number:
                    print(f"Line {finding.line_number}: {finding.message}")
                else:
                    print(finding.message)

                if finding.code_snippet:
                    print(f"  → {finding.code_snippet}")

        print("\n")


class CodeReviewer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.report = ReviewReport(file_path=file_path)
        self.content = ""
        self.lines = []
        self.tree = None

    def review(self) -> ReviewReport:
        """Run all review checks."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
        except Exception as e:
            self.report.add_finding(
                Severity.CRITICAL,
                "Error",
                f"Failed to read file: {e}"
            )
            return self.report

        # Try to parse AST
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            self.report.add_finding(
                Severity.CRITICAL,
                "Syntax",
                f"Syntax error: {e}"
            )
            return self.report

        # Run all checks
        self._check_security()
        self._check_performance()
        self._check_style()
        self._check_good_practices()

        return self.report

    def _check_security(self):
        """Check for security vulnerabilities."""

        # 1. Hardcoded secrets/API keys
        secret_patterns = [
            (r'api[_-]?key\s*=\s*["\'](?!your_|test_)[A-Za-z0-9]{20,}["\']',
             "Hardcoded API key detected"),
            (r'password\s*=\s*["\'][^"\']{3,}["\']',
             "Hardcoded password detected"),
            (r'secret\s*=\s*["\'](?!your_)[^"\']{10,}["\']',
             "Hardcoded secret detected"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, msg in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if it's from environment variable
                    if 'os.getenv' not in line and 'os.environ' not in line:
                        self.report.add_finding(
                            Severity.CRITICAL,
                            "Security",
                            msg,
                            i,
                            line.strip()
                        )

        # 2. SQL Injection risk
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Call):
                    # Check for string formatting in SQL queries
                    if hasattr(node.func, 'attr') and node.func.attr in ['execute', 'executemany']:
                        if node.args:
                            arg = node.args[0]
                            # Check if using f-string or % formatting
                            if isinstance(arg, ast.JoinedStr):  # f-string
                                self.report.add_finding(
                                    Severity.CRITICAL,
                                    "Security",
                                    "Potential SQL injection: Using f-string in SQL query. Use parameterized queries instead.",
                                    node.lineno
                                )

        # 3. eval() usage
        for i, line in enumerate(self.lines, 1):
            if re.search(r'\beval\s*\(', line):
                self.report.add_finding(
                    Severity.CRITICAL,
                    "Security",
                    "Using eval() is dangerous and can execute arbitrary code",
                    i,
                    line.strip()
                )

        # 4. Shell injection risk
        shell_risk_patterns = [
            (r'os\.system\s*\([^)]*\+[^)]*\)', "os.system with string concatenation"),
            (r'subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True[^)]*\+',
             "subprocess with shell=True and concatenation"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, msg in shell_risk_patterns:
                if re.search(pattern, line):
                    self.report.add_finding(
                        Severity.CRITICAL,
                        "Security",
                        f"Shell injection risk: {msg}",
                        i,
                        line.strip()
                    )

        # 5. XSS risk in web frameworks
        xss_patterns = [
            r'unsafe_allow_html\s*=\s*True',
            r'st\.markdown\([^)]*unsafe_allow_html\s*=\s*True',
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern in xss_patterns:
                if re.search(pattern, line):
                    # Check if the content is user-controlled
                    if any(var in line for var in ['request', 'input', 'form', 'query', 'params']):
                        self.report.add_finding(
                            Severity.CRITICAL,
                            "Security",
                            "Potential XSS: Using unsafe_allow_html with user input",
                            i,
                            line.strip()
                        )

    def _check_performance(self):
        """Check for performance issues."""

        # 1. Inefficient loops
        for i, line in enumerate(self.lines, 1):
            # List append in loop without pre-allocation hint
            if re.search(r'for\s+\w+\s+in.*:\s*$', line):
                next_lines = self.lines[i:min(i+5, len(self.lines))]
                has_list_append = any(re.search(r'\.append\(', l) for l in next_lines)
                has_list_extend = any(re.search(r'\.extend\(', l) for l in next_lines)

                if has_list_append and 'range(1000' in line or 'range(10000' in line:
                    self.report.add_finding(
                        Severity.SUGGESTION,
                        "Performance",
                        "Consider using list comprehension instead of append in large loop",
                        i,
                        line.strip()
                    )

        # 2. Repeated function calls in loops
        for i, line in enumerate(self.lines, 1):
            match = re.search(r'for\s+\w+\s+in\s+range\(([^)]+)\)', line)
            if match:
                next_lines = self.lines[i:min(i+10, len(self.lines))]
                # Look for repeated len(), max(), min() calls
                for j, next_line in enumerate(next_lines):
                    if re.search(r'(len|max|min)\([^)]+\)', next_line):
                        self.report.add_finding(
                            Severity.SUGGESTION,
                            "Performance",
                            "Function call inside loop might be inefficient. Consider storing result before loop.",
                            i + j
                        )
                        break

        # 3. Database query in loop
        for i, line in enumerate(self.lines, 1):
            if re.search(r'for\s+\w+\s+in', line):
                next_lines = self.lines[i:min(i+10, len(self.lines))]
                for j, next_line in enumerate(next_lines):
                    if any(keyword in next_line for keyword in ['execute(', 'query(', 'get_cache(']):
                        self.report.add_finding(
                            Severity.CRITICAL,
                            "Performance",
                            "Database query inside loop (N+1 problem). Consider bulk query or caching.",
                            i + j,
                            next_line.strip()
                        )
                        break

        # 4. Memory leaks - unclosed files/connections
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, 'id'):
                        if node.func.id == 'open':
                            # Check if it's in a 'with' statement
                            # This is a simplified check
                            self.report.add_finding(
                                Severity.SUGGESTION,
                                "Performance",
                                "Consider using 'with' statement for file operations to ensure proper closure",
                                node.lineno
                            )

        # 5. Inefficient string concatenation
        for i, line in enumerate(self.lines, 1):
            if '+=' in line and 'str' in line.lower():
                self.report.add_finding(
                    Severity.SUGGESTION,
                    "Performance",
                    "String concatenation with += in loop is inefficient. Use list and join() instead.",
                    i,
                    line.strip()
                )

        # 6. Good: Caching implementation
        cache_indicators = ['cache', 'memoize', '@lru_cache', '@cache']
        for i, line in enumerate(self.lines, 1):
            if any(indicator in line.lower() for indicator in cache_indicators):
                self.report.add_finding(
                    Severity.GOOD,
                    "Performance",
                    "Good use of caching mechanism",
                    i
                )

    def _check_style(self):
        """Check for style violations."""

        # 1. Line length (PEP 8: 79 chars, we'll use 100 as lenient)
        long_lines = []
        for i, line in enumerate(self.lines, 1):
            if len(line) > 120 and not line.strip().startswith('#'):
                long_lines.append(i)

        if long_lines:
            self.report.add_finding(
                Severity.SUGGESTION,
                "Style",
                f"Lines exceed 120 characters: {', '.join(map(str, long_lines[:5]))}" +
                (f" and {len(long_lines)-5} more" if len(long_lines) > 5 else "")
            )

        # 2. Naming conventions
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    # Function names should be snake_case
                    if not re.match(r'^[a-z_][a-z0-9_]*$', node.name) and not node.name.startswith('_'):
                        if node.name[0].isupper():
                            self.report.add_finding(
                                Severity.SUGGESTION,
                                "Style",
                                f"Function name '{node.name}' should be snake_case (PEP 8)",
                                node.lineno
                            )

                if isinstance(node, ast.ClassDef):
                    # Class names should be PascalCase
                    if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                        self.report.add_finding(
                            Severity.SUGGESTION,
                            "Style",
                            f"Class name '{node.name}' should be PascalCase (PEP 8)",
                            node.lineno
                        )

        # 3. Multiple imports on one line
        for i, line in enumerate(self.lines, 1):
            if line.strip().startswith('import ') and ',' in line:
                self.report.add_finding(
                    Severity.SUGGESTION,
                    "Style",
                    "Multiple imports on one line. Split into separate lines (PEP 8)",
                    i,
                    line.strip()
                )

        # 4. Unused imports
        if self.tree:
            imports = set()
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.add(alias.name)

            # Simple check: if import name doesn't appear elsewhere in code
            for imp in imports:
                # Count occurrences (excluding import line itself)
                count = sum(1 for line in self.lines if imp in line and not line.strip().startswith('import') and not line.strip().startswith('from'))
                if count == 0:
                    self.report.add_finding(
                        Severity.SUGGESTION,
                        "Style",
                        f"Potentially unused import: {imp}"
                    )

        # 5. Trailing whitespace
        trailing_ws_lines = [i for i, line in enumerate(self.lines, 1) if line.rstrip() != line and line.strip()]
        if trailing_ws_lines:
            self.report.add_finding(
                Severity.SUGGESTION,
                "Style",
                f"Trailing whitespace found on {len(trailing_ws_lines)} lines"
            )

        # 6. Good: Type hints usage
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    if node.returns or any(arg.annotation for arg in node.args.args):
                        self.report.add_finding(
                            Severity.GOOD,
                            "Style",
                            f"Good use of type hints in '{node.name}'",
                            node.lineno
                        )

    def _check_good_practices(self):
        """Identify good practices in the code."""

        # 1. Error handling
        try_except_count = self.content.count('try:')
        if try_except_count > 0:
            self.report.add_finding(
                Severity.GOOD,
                "Best Practice",
                f"Proper error handling with {try_except_count} try-except block(s)"
            )

        # 2. Docstrings
        if self.tree:
            funcs_with_docstrings = 0
            total_funcs = 0

            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    total_funcs += 1
                    if ast.get_docstring(node):
                        funcs_with_docstrings += 1

            if total_funcs > 0:
                ratio = funcs_with_docstrings / total_funcs
                if ratio > 0.7:
                    self.report.add_finding(
                        Severity.GOOD,
                        "Best Practice",
                        f"Good documentation: {funcs_with_docstrings}/{total_funcs} functions have docstrings"
                    )
                elif ratio < 0.3:
                    self.report.add_finding(
                        Severity.SUGGESTION,
                        "Best Practice",
                        f"Consider adding docstrings: Only {funcs_with_docstrings}/{total_funcs} functions documented"
                    )

        # 3. Environment variables for secrets
        if 'os.getenv' in self.content or 'os.environ' in self.content:
            self.report.add_finding(
                Severity.GOOD,
                "Security",
                "Properly using environment variables for sensitive data"
            )

        # 4. Logging
        if 'logging.' in self.content or 'logger.' in self.content:
            self.report.add_finding(
                Severity.GOOD,
                "Best Practice",
                "Using logging module for better debugging"
            )

        # 5. Context managers
        with_count = self.content.count('with ')
        if with_count > 0:
            self.report.add_finding(
                Severity.GOOD,
                "Best Practice",
                f"Using context managers ({with_count} 'with' statements)"
            )


def review_file(file_path: str) -> ReviewReport:
    """Review a single file."""
    reviewer = CodeReviewer(file_path)
    return reviewer.review()


def review_directory(directory: str = ".") -> List[ReviewReport]:
    """Review all Python files in directory."""
    reports = []

    # Skip test files, migrations, and virtual environments
    skip_patterns = ['venv', '.venv', '__pycache__', '.git', '.pytest_cache', 'migrations']

    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in skip_patterns)]

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                reports.append(review_file(file_path))

    return reports


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Review specific file
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        report = review_file(file_path)
        report.print_report()
    else:
        # Review entire project
        print("🔍 Reviewing all Python files in project...\n")
        reports = review_directory(".")

        total_critical = 0
        total_suggestions = 0
        total_good = 0

        for report in reports:
            report.print_report()

            # Count totals
            for finding in report.findings:
                if finding.severity == Severity.CRITICAL:
                    total_critical += 1
                elif finding.severity == Severity.SUGGESTION:
                    total_suggestions += 1
                elif finding.severity == Severity.GOOD:
                    total_good += 1

        # Summary
        print(f"\n{'='*80}")
        print("📊 SUMMARY")
        print(f"{'='*80}")
        print(f"Files reviewed: {len(reports)}")
        print(f"🔴 Critical issues: {total_critical}")
        print(f"🟡 Suggestions: {total_suggestions}")
        print(f"🟢 Good practices: {total_good}")
        print()


if __name__ == "__main__":
    main()
