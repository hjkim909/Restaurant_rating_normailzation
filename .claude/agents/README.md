# Sub-Agent System

## How it works

```
User: "API 보안 체크해줘"
  ↓
Claude reads: .claude/agents/api_security.md
  ↓
Claude follows the checklist
  ↓
Claude reports findings
```

## Available agents

| Command | Agent File | Purpose |
|---------|-----------|---------|
| "API 보안 체크" | `api_security.md` | Check API keys, SQL injection, XSS |
| "좌표 검증" | `coordinate_validation.md` | Validate Naver coordinate conversion |
| "DB 성능" | `db_performance.md` | Analyze cache efficiency, N+1 queries |
| "UX 리뷰" | `ux_review.md` | Review Streamlit user experience |

## Agent format

Each agent is **1-2KB**, focused, action-oriented:

```markdown
# Agent Name

## When to use
- User asks: "keywords"

## Check these files
- file1.py
- file2.py

## Critical checks
### 1. Issue name
❌ Bad example
✅ Good example

### 2. Issue name
...

## Output format
What the report should look like
```

## For Claude

When user asks for a check:
1. Read the relevant agent MD file
2. Read the files it mentions
3. Follow the checklist
4. Report in the specified format
5. Keep it concise

## Adding new agents

Keep them short:
- 5-10 critical checks max
- Code examples for each
- Clear ❌/✅ patterns
- Specific line numbers in output
