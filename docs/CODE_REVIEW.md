# Code Review Tool

Automated code review tool that analyzes Python files for security vulnerabilities, performance issues, and style violations.

## Usage

### Review a Single File
```bash
python scripts/code_review.py backend/naver_api.py
```

### Review Entire Project
```bash
python scripts/code_review.py
```

### Review Specific Directory
```bash
cd backend && python ../scripts/code_review.py
```

## What It Checks

### 🔴 Critical Issues

#### Security
- **Hardcoded secrets**: Detects API keys, passwords, or secrets in code (should use environment variables)
- **SQL injection**: Identifies f-strings or string concatenation in SQL queries
- **eval() usage**: Flags dangerous eval() calls that can execute arbitrary code
- **Shell injection**: Detects os.system or subprocess with shell=True and string concatenation
- **XSS vulnerabilities**: Identifies unsafe_allow_html with user input in Streamlit

#### Performance
- **N+1 query problem**: Database queries inside loops
- **Inefficient database access**: Repeated DB calls that should be batched

### 🟡 Suggestions

#### Performance
- **Inefficient loops**: List append in large loops (suggest list comprehension)
- **Repeated function calls**: len(), max(), min() called inside loops
- **Memory leaks**: Files/connections not using 'with' statement
- **String concatenation**: Using += for strings in loops (suggest join())

#### Style (PEP 8)
- **Line length**: Lines exceeding 120 characters
- **Naming conventions**: snake_case for functions, PascalCase for classes
- **Multiple imports**: Import statements with commas
- **Unused imports**: Imported but never used modules
- **Trailing whitespace**: Extra spaces at end of lines

#### Best Practices
- **Missing docstrings**: Functions without documentation
- **Low documentation coverage**: Less than 30% of functions documented

### 🟢 Good Practices

#### Performance
- **Caching implementation**: Using @cache, @lru_cache, or custom caching
- **Context managers**: Proper use of 'with' statements

#### Security
- **Environment variables**: Using os.getenv() for secrets

#### Best Practices
- **Error handling**: Try-except blocks for robust code
- **Logging**: Using logging module instead of print()
- **Documentation**: 70%+ functions have docstrings
- **Type hints**: Functions with type annotations

## Example Output

```
================================================================================
📄 File: backend/naver_api.py
================================================================================

🔴 Critical (1 items)
--------------------------------------------------------------------------------

[Security]
Line 145: Hardcoded API key detected
  → api_key = "abc123def456"

🟡 Suggestion (3 items)
--------------------------------------------------------------------------------

[Performance]
Line 89: Database query inside loop (N+1 problem). Consider bulk query or caching.
  → data = api.search_places(query, display=5)

[Style]
Lines exceed 120 characters: 23, 45, 67, 89, 102

[Best Practice]
Consider adding docstrings: Only 2/7 functions documented

🟢 Good (5 items)
--------------------------------------------------------------------------------

[Performance]
Good use of caching mechanism

[Security]
Properly using environment variables for sensitive data

[Best Practice]
Using logging module for better debugging
```

## Integration Tips

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python scripts/code_review.py > /tmp/review.txt
if grep -q "🔴 Critical" /tmp/review.txt; then
    cat /tmp/review.txt
    echo "❌ Critical issues found. Please fix before committing."
    exit 1
fi
```

### CI/CD Pipeline
Add to GitHub Actions or similar:
```yaml
- name: Code Review
  run: |
    python scripts/code_review.py
    if [ $? -ne 0 ]; then exit 1; fi
```

### IDE Integration
For VS Code, create a task in `.vscode/tasks.json`:
```json
{
    "label": "Code Review",
    "type": "shell",
    "command": "python scripts/code_review.py ${file}",
    "problemMatcher": []
}
```

## Customization

To customize the checks, edit `scripts/code_review.py`:

- **Add new patterns**: Modify `secret_patterns`, `shell_risk_patterns`, etc.
- **Adjust severity**: Change Severity levels for specific findings
- **Skip directories**: Modify `skip_patterns` in `review_directory()`
- **Line length limit**: Change the 120 character threshold in `_check_style()`

## Project-Specific Checks

This tool is aware of the project's context:

1. **Naver API integration**: Checks for proper API key handling
2. **SQLite caching**: Validates safe query construction
3. **Streamlit UI**: Checks for XSS vulnerabilities with unsafe_allow_html
4. **Coordinate handling**: Ensures proper error handling in geo_utils

## False Positives

Some findings may be intentional:

- **Caching comments**: Tool may flag many caching references as "good" - this is expected for this project
- **Unused imports**: Some imports may be used dynamically (check carefully)
- **Line length**: Long regex patterns or URLs are acceptable exceptions

## Limitations

- **AST-based**: May miss runtime issues or complex logic problems
- **No execution**: Doesn't run the code, so can't catch runtime errors
- **Pattern matching**: Uses regex for some checks, which can have false positives
- **No external analysis**: Doesn't check dependencies for vulnerabilities

For comprehensive security audits, also use:
- `bandit` - Python security linter
- `safety` - Check dependencies for known vulnerabilities
- `pylint` - More comprehensive style checking
