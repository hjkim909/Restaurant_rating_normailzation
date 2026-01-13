# Workflows

Workflows are step-by-step guides for common development tasks.

Unlike sub-agents (which check/validate), workflows guide you through multi-step processes.

## Available workflows

| Task | Workflow File |
|------|--------------|
| Adding new feature | `feature_addition.md` |
| Fixing bugs | `bug_fix.md` (TODO) |
| Refactoring | `refactoring.md` (TODO) |
| Deployment | `deployment.md` (TODO) |

## When to use workflows

**Use workflows when:**
- User requests complex multi-file changes
- You need a consistent process to follow
- Multiple docs need updating
- Multiple validation steps required

**Example:**
```
User: "카카오 지도 API도 추가해줘"

Claude:
1. Reads .claude/workflows/feature_addition.md
2. Follows steps:
   - Clarify (which features of Kakao API?)
   - Assess impact (new API client, caching, UI changes)
   - Enter plan mode
   - Implement
   - Update docs (PRD, CLAUDE.md, requirements.txt)
   - Run "API 보안 체크"
   - Commit
```

## Creating new workflows

Keep workflows:
- **Step-by-step**: Clear sequence
- **Checkable**: Use checkboxes
- **Example-driven**: Show concrete examples
- **Short**: 100-200 lines max
- **Actionable**: Every step is something to do

Format:
```markdown
# [Workflow Name]

## When to use
[Trigger conditions]

## Steps
1. Step one
2. Step two
   - Sub-step
   - Sub-step
3. Step three

## Example
[Concrete example]

## Checklist
- [ ] Item 1
- [ ] Item 2
```
