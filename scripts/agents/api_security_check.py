#!/usr/bin/env python3
"""
API Security Agent - API 엔드포인트 보안 검사 전문 서브에이전트

네이버 API 통합 및 외부 API 호출의 보안 취약점을 검사합니다.

Usage:
    python scripts/agents/api_security_check.py [file_path]
    python scripts/agents/api_security_check.py --verbose
"""

import os
import re
import ast
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    CRITICAL = "🔴 CRITICAL"
    WARNING = "🟡 WARNING"
    INFO = "🟢 GOOD"


@dataclass
class SecurityFinding:
    severity: Severity
    category: str
    message: str
    line_number: int = 0
    code_snippet: str = ""
    fix_suggestion: str = ""
    cwe_id: str = ""  # Common Weakness Enumeration


@dataclass
class SecurityReport:
    file_path: str
    findings: List[SecurityFinding] = field(default_factory=list)
    risk_score: int = 100  # 100 = safe, 0 = critical

    def add_finding(self, severity: Severity, category: str, message: str,
                    line_number: int = 0, code_snippet: str = "",
                    fix_suggestion: str = "", cwe_id: str = ""):
        finding = SecurityFinding(
            severity=severity,
            category=category,
            message=message,
            line_number=line_number,
            code_snippet=code_snippet,
            fix_suggestion=fix_suggestion,
            cwe_id=cwe_id
        )
        self.findings.append(finding)

        # Update risk score
        if severity == Severity.CRITICAL:
            self.risk_score -= 20
        elif severity == Severity.WARNING:
            self.risk_score -= 5

    def print_report(self, verbose=False):
        print(f"\n{'='*80}")
        print(f"🔒 API Security Report")
        print(f"{'='*80}")
        print(f"File: {self.file_path}")
        print(f"Risk Score: {max(0, self.risk_score)}/100", end="")

        if self.risk_score >= 80:
            print(" ✅ (Low Risk)")
        elif self.risk_score >= 60:
            print(" ⚠️  (Moderate Risk)")
        else:
            print(" 🚨 (High Risk)")
        print()

        # Group by severity
        by_severity = {
            Severity.CRITICAL: [],
            Severity.WARNING: [],
            Severity.INFO: []
        }

        for finding in self.findings:
            by_severity[finding.severity].append(finding)

        # Print summary
        print(f"🔴 Critical Issues: {len(by_severity[Severity.CRITICAL])}")
        print(f"🟡 Warnings: {len(by_severity[Severity.WARNING])}")
        print(f"🟢 Good Practices: {len(by_severity[Severity.INFO])}")
        print()

        # Print details
        for severity in [Severity.CRITICAL, Severity.WARNING, Severity.INFO]:
            items = by_severity[severity]
            if not items:
                continue

            print(f"\n{severity.value}")
            print("-" * 80)

            for finding in items:
                print(f"\n[{finding.category}]", end="")
                if finding.cwe_id:
                    print(f" (CWE-{finding.cwe_id})", end="")
                print()

                if finding.line_number:
                    print(f"Line {finding.line_number}: {finding.message}")
                else:
                    print(finding.message)

                if finding.code_snippet and verbose:
                    print(f"  Code: {finding.code_snippet}")

                if finding.fix_suggestion and severity != Severity.INFO:
                    print(f"  Fix: {finding.fix_suggestion}")

        print("\n")


class APISecurityAgent:
    """API 보안 검사 전문 에이전트"""

    def __init__(self, file_path: str, verbose: bool = False):
        self.file_path = file_path
        self.verbose = verbose
        self.report = SecurityReport(file_path=file_path)
        self.content = ""
        self.lines = []
        self.tree = None

    def analyze(self) -> SecurityReport:
        """보안 분석 실행"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
                self.lines = self.content.split('\n')
        except Exception as e:
            self.report.add_finding(
                Severity.CRITICAL,
                "File Access",
                f"Failed to read file: {e}"
            )
            return self.report

        # Parse AST
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            self.report.add_finding(
                Severity.CRITICAL,
                "Syntax Error",
                f"Cannot parse file: {e}"
            )
            return self.report

        # Run security checks
        self._check_api_keys()
        self._check_https()
        self._check_sql_injection()
        self._check_xss()
        self._check_rate_limiting()
        self._check_input_validation()
        self._check_error_handling()
        self._check_response_validation()
        self._check_caching_security()
        self._check_good_practices()
        self._check_naver_api_specific()

        return self.report

    def _check_api_keys(self):
        """API 키 관리 검사"""
        # 1. Hardcoded API keys
        key_patterns = [
            (r'(client_id|api_key|secret|password)\s*=\s*["\'](?!your_|test_|mock_)[A-Za-z0-9]{20,}["\']',
             "Hardcoded API credential detected",
             "Use environment variables: os.getenv('NAVER_CLIENT_ID')",
             "798"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, msg, fix, cwe in key_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip if using environment variable
                    if 'os.getenv' in line or 'os.environ' in line:
                        continue

                    self.report.add_finding(
                        Severity.CRITICAL,
                        "API Key Security",
                        msg,
                        i,
                        line.strip(),
                        fix,
                        cwe
                    )

        # 2. API keys in logs
        log_pattern = r'(logging|logger|print|st\.write).*\(.*["\'][^"\']*\{[^}]*(client_id|secret|key|password)'
        for i, line in enumerate(self.lines, 1):
            if re.search(log_pattern, line, re.IGNORECASE):
                self.report.add_finding(
                    Severity.CRITICAL,
                    "API Key Security",
                    "Potential API key exposure in logging",
                    i,
                    line.strip(),
                    "Mask sensitive data: f'{api_key[:4]}****'",
                    "532"
                )

    def _check_https(self):
        """HTTPS 강제 검사"""
        # HTTP URLs
        http_pattern = r'["\']http://[^"\']*["\']'
        for i, line in enumerate(self.lines, 1):
            if re.search(http_pattern, line):
                # Skip comments and localhost
                if line.strip().startswith('#') or 'localhost' in line or '127.0.0.1' in line:
                    continue

                self.report.add_finding(
                    Severity.CRITICAL,
                    "Transport Security",
                    "Using HTTP instead of HTTPS",
                    i,
                    line.strip(),
                    "Change to https://",
                    "319"
                )

        # SSL verification disabled
        if 'verify=False' in self.content or 'verify = False' in self.content:
            for i, line in enumerate(self.lines, 1):
                if 'verify=False' in line or 'verify = False' in line:
                    self.report.add_finding(
                        Severity.CRITICAL,
                        "Transport Security",
                        "SSL certificate verification disabled",
                        i,
                        line.strip(),
                        "Remove verify=False parameter",
                        "295"
                    )

    def _check_sql_injection(self):
        """SQL Injection 검사"""
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.Call):
                    # execute() 호출 찾기
                    if hasattr(node.func, 'attr') and node.func.attr in ['execute', 'executemany']:
                        if node.args:
                            arg = node.args[0]
                            # f-string 사용 체크
                            if isinstance(arg, ast.JoinedStr):
                                self.report.add_finding(
                                    Severity.CRITICAL,
                                    "SQL Injection",
                                    "Using f-string in SQL query - SQL injection risk",
                                    node.lineno,
                                    "",
                                    "Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id=?', (id,))",
                                    "89"
                                )
                            # % formatting 체크
                            elif isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                                self.report.add_finding(
                                    Severity.CRITICAL,
                                    "SQL Injection",
                                    "Using % formatting in SQL query - SQL injection risk",
                                    node.lineno,
                                    "",
                                    "Use parameterized queries with ? placeholders",
                                    "89"
                                )

    def _check_xss(self):
        """XSS 취약점 검사"""
        # Streamlit unsafe_allow_html
        for i, line in enumerate(self.lines, 1):
            if 'unsafe_allow_html=True' in line or 'unsafe_allow_html = True' in line:
                # 이전 몇 줄에 사용자 입력이 있는지 체크
                context = '\n'.join(self.lines[max(0, i-5):i])
                user_input_indicators = ['request', 'input(', 'form', 'query', 'params', 'args', 'st.text_input']

                if any(indicator in context for indicator in user_input_indicators):
                    self.report.add_finding(
                        Severity.CRITICAL,
                        "XSS Vulnerability",
                        "Using unsafe_allow_html with potential user input",
                        i,
                        line.strip(),
                        "Sanitize HTML: clean_html = re.sub('<.*?>', '', user_input)",
                        "79"
                    )

        # HTML cleaning 체크 (Good practice)
        if 're.sub' in self.content and '<.*?>' in self.content:
            self.report.add_finding(
                Severity.INFO,
                "XSS Prevention",
                "HTML sanitization detected (good practice)"
            )

    def _check_rate_limiting(self):
        """Rate limiting 검사"""
        has_rate_limit_check = False
        has_429_handler = False

        for i, line in enumerate(self.lines, 1):
            # Rate limit 추적
            if any(keyword in line.lower() for keyword in ['rate_limit', 'quota', 'call_count', 'request_count']):
                has_rate_limit_check = True

            # 429 처리
            if '429' in line or 'Too Many Requests' in line:
                has_429_handler = True

        if not has_rate_limit_check and 'requests.get' in self.content:
            self.report.add_finding(
                Severity.WARNING,
                "Rate Limiting",
                "No rate limiting check detected",
                0,
                "",
                "Add rate limit tracking: if self.call_count > LIMIT: raise RateLimitError()"
            )

        if not has_429_handler and 'requests.get' in self.content:
            self.report.add_finding(
                Severity.WARNING,
                "Rate Limiting",
                "No 429 (Too Many Requests) handler detected",
                0,
                "",
                "Add: if response.status_code == 429: time.sleep(retry_after)"
            )

        if has_rate_limit_check:
            self.report.add_finding(
                Severity.INFO,
                "Rate Limiting",
                "Rate limiting implementation detected"
            )

    def _check_input_validation(self):
        """입력 검증 검사"""
        if self.tree:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.FunctionDef):
                    # 함수 파라미터가 있는데 검증이 없는지 체크
                    if node.args.args:
                        func_body = ast.get_source_segment(self.content, node)
                        if func_body:
                            # 간단한 휴리스틱: raise ValueError나 assert가 있으면 검증하는 것으로 간주
                            has_validation = 'raise ValueError' in func_body or 'assert' in func_body or 'if not' in func_body

                            # API 관련 함수만 체크
                            if 'api' in node.name.lower() or 'search' in node.name.lower():
                                if not has_validation:
                                    self.report.add_finding(
                                        Severity.WARNING,
                                        "Input Validation",
                                        f"Function '{node.name}' may lack input validation",
                                        node.lineno,
                                        "",
                                        "Add: if not param or len(param) < min_length: raise ValueError('Invalid input')"
                                    )

    def _check_error_handling(self):
        """에러 핸들링 검사"""
        # API 키 노출 in exception
        for i, line in enumerate(self.lines, 1):
            if 'except' in line:
                next_lines = self.lines[i:min(i+5, len(self.lines))]
                for j, next_line in enumerate(next_lines):
                    # 에러를 그대로 사용자에게 보여주는 경우
                    if any(keyword in next_line for keyword in ['st.error(str(e))', 'st.error(f', 'print(e)']):
                        self.report.add_finding(
                            Severity.WARNING,
                            "Error Handling",
                            "Exception details exposed to user",
                            i + j,
                            next_line.strip(),
                            "Log the error but show generic message to user"
                        )

        # Timeout 설정 체크
        if 'requests.get' in self.content or 'requests.post' in self.content:
            has_timeout = 'timeout=' in self.content
            if not has_timeout:
                self.report.add_finding(
                    Severity.WARNING,
                    "Error Handling",
                    "No timeout set for HTTP requests",
                    0,
                    "",
                    "Add timeout parameter: requests.get(url, timeout=10)"
                )

        # try-except 사용 (Good)
        try_count = self.content.count('try:')
        if try_count > 0:
            self.report.add_finding(
                Severity.INFO,
                "Error Handling",
                f"Proper error handling with {try_count} try-except block(s)"
            )

    def _check_response_validation(self):
        """API 응답 검증"""
        # response.json() 사용 후 검증
        if 'response.json()' in self.content:
            # 'items' in data 같은 검증이 있는지 확인
            has_validation = 'in data' in self.content or 'in response' in self.content or '.get(' in self.content

            if not has_validation:
                self.report.add_finding(
                    Severity.WARNING,
                    "Response Validation",
                    "API response structure not validated",
                    0,
                    "",
                    "Add: if 'items' not in data: raise ValueError('Invalid response')"
                )
            else:
                self.report.add_finding(
                    Severity.INFO,
                    "Response Validation",
                    "API response validation detected"
                )

        # Type conversion with error handling
        for i, line in enumerate(self.lines, 1):
            if 'float(' in line or 'int(' in line:
                # 이전/다음 줄에 try-except가 있는지 확인
                context = '\n'.join(self.lines[max(0, i-2):min(i+2, len(self.lines))])
                if 'try' not in context and 'except' not in context:
                    self.report.add_finding(
                        Severity.WARNING,
                        "Response Validation",
                        "Type conversion without error handling",
                        i,
                        line.strip(),
                        "Wrap in try-except (ValueError, TypeError)"
                    )

    def _check_caching_security(self):
        """캐싱 보안 검사"""
        # 민감 정보 캐싱 체크
        cache_patterns = ['cache', 'save_cache', 'db.save', 'json.dump']

        for i, line in enumerate(self.lines, 1):
            if any(pattern in line for pattern in cache_patterns):
                # 다음 몇 줄에 민감한 키워드가 있는지 확인
                next_lines = self.lines[i:min(i+10, len(self.lines))]
                sensitive_keywords = ['client_id', 'secret', 'password', 'token', 'api_key']

                for keyword in sensitive_keywords:
                    if any(keyword in l for l in next_lines):
                        self.report.add_finding(
                            Severity.CRITICAL,
                            "Caching Security",
                            f"Potential caching of sensitive data: {keyword}",
                            i,
                            line.strip(),
                            "Never cache API keys, tokens, or passwords",
                            "311"
                        )
                        break

        # 캐시 만료 체크 (Good)
        if 'expiry' in self.content or 'expire' in self.content or 'time.time()' in self.content:
            self.report.add_finding(
                Severity.INFO,
                "Caching Security",
                "Cache expiration mechanism detected"
            )

    def _check_good_practices(self):
        """좋은 관행 체크"""
        # 환경 변수 사용
        if 'os.getenv' in self.content or 'os.environ' in self.content:
            self.report.add_finding(
                Severity.INFO,
                "Best Practice",
                "Using environment variables for configuration"
            )

        # Logging 사용
        if 'logging.' in self.content or 'logger.' in self.content:
            self.report.add_finding(
                Severity.INFO,
                "Best Practice",
                "Using logging module"
            )

        # HTTPS 강제
        if 'https://' in self.content and 'http://' not in self.content:
            self.report.add_finding(
                Severity.INFO,
                "Best Practice",
                "HTTPS enforced for all API calls"
            )

    def _check_naver_api_specific(self):
        """네이버 API 특화 검사"""
        # Client ID/Secret 쌍 체크
        has_client_id = 'NAVER_CLIENT_ID' in self.content
        has_client_secret = 'NAVER_CLIENT_SECRET' in self.content

        if has_client_id and not has_client_secret:
            self.report.add_finding(
                Severity.CRITICAL,
                "Naver API",
                "CLIENT_ID found but CLIENT_SECRET missing",
                0,
                "",
                "Both CLIENT_ID and CLIENT_SECRET are required"
            )
        elif has_client_secret and not has_client_id:
            self.report.add_finding(
                Severity.CRITICAL,
                "Naver API",
                "CLIENT_SECRET found but CLIENT_ID missing",
                0,
                "",
                "Both CLIENT_ID and CLIENT_SECRET are required"
            )

        # 좌표 범위 검증
        for i, line in enumerate(self.lines, 1):
            if 'mapx' in line or 'mapy' in line:
                # 다음 몇 줄에서 범위 체크가 있는지 확인
                next_lines = '\n'.join(self.lines[i:min(i+5, len(self.lines))])
                has_range_check = any(keyword in next_lines for keyword in ['>', '<', 'range', 'if', 'isfinite'])

                if not has_range_check and 'float(' in line:
                    self.report.add_finding(
                        Severity.WARNING,
                        "Naver API",
                        "Coordinate conversion without range validation",
                        i,
                        line.strip(),
                        "Check: if 120000000 < mapx < 130000000 and 30000000 < mapy < 40000000"
                    )


def analyze_file(file_path: str, verbose: bool = False) -> SecurityReport:
    """파일 분석"""
    agent = APISecurityAgent(file_path, verbose)
    return agent.analyze()


def main():
    parser = argparse.ArgumentParser(description='API Security Agent - 보안 검사 전문 에이전트')
    parser.add_argument('file', nargs='?', help='Python file to analyze')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--all', action='store_true', help='Analyze all Python files')

    args = parser.parse_args()

    if args.all or not args.file:
        # 전체 프로젝트 검사
        print("🔍 Scanning entire project for API security issues...\n")

        reports = []
        skip_patterns = ['venv', '.venv', '__pycache__', '.git', '.pytest_cache', 'migrations', 'test_']

        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in skip_patterns)]

            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    report = analyze_file(file_path, args.verbose)
                    reports.append(report)

        # 전체 통계
        total_critical = sum(len([f for f in r.findings if f.severity == Severity.CRITICAL]) for r in reports)
        total_warnings = sum(len([f for f in r.findings if f.severity == Severity.WARNING]) for r in reports)
        avg_risk = sum(r.risk_score for r in reports) / len(reports) if reports else 100

        # 각 파일 리포트
        for report in reports:
            if report.findings:  # 발견사항이 있는 경우만 출력
                report.print_report(args.verbose)

        # 요약
        print(f"\n{'='*80}")
        print("📊 PROJECT SECURITY SUMMARY")
        print(f"{'='*80}")
        print(f"Files Scanned: {len(reports)}")
        print(f"🔴 Total Critical Issues: {total_critical}")
        print(f"🟡 Total Warnings: {total_warnings}")
        print(f"Average Risk Score: {avg_risk:.1f}/100")

        if total_critical > 0:
            print("\n⚠️  RECOMMENDATION: Fix critical issues before deployment!")
            sys.exit(1)
        elif avg_risk < 70:
            print("\n⚠️  RECOMMENDATION: Address warnings to improve security posture.")
        else:
            print("\n✅ Security status: Good")

    else:
        # 단일 파일 검사
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)

        report = analyze_file(args.file, args.verbose)
        report.print_report(args.verbose)

        # Exit code
        critical_count = len([f for f in report.findings if f.severity == Severity.CRITICAL])
        if critical_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
