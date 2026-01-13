# Feature Addition Workflow

## When to use
User requests: "새 기능 추가해줘", "~기능 만들어줘", "~할 수 있게 해줘"

## Steps

### 1. Clarify requirements
```
Ask user:
- What exactly should this feature do?
- Who will use it?
- Any specific constraints or preferences?
```

### 2. Assess impact
Read these files to understand current architecture:
- `docs/PRD.md` - Current features
- `CLAUDE.md` - Architecture overview
- Related backend files

### 3. Enter Plan Mode (if non-trivial)
```
Use EnterPlanMode for:
- Features touching 3+ files
- New API integrations
- Database schema changes
- UI flow changes
```

### 4. Implement
Follow existing patterns:
- Backend logic in `backend/`
- UI in `app.py`
- Keep functions small and focused
- Match existing naming conventions

### 5. Update documentation (CRITICAL)

**Always check these files:**

```markdown
✓ docs/PRD.md
  - Add to feature list if user-facing
  - Update "MVP 기능 요구사항" section

✓ CLAUDE.md
  - Update "Architecture" if adding new modules
  - Update "Common Gotchas" if introducing tricky logic
  - Add to "Commands" if new script

✓ README.md
  - Update "주요 기능" if user-visible
  - Update "시작하기" if setup changes
  - Update "프로젝트 구조" if new folders

✓ requirements.txt
  - Add new packages with version pins
  - Run: pip freeze | grep package_name

✓ .claude/code_review_rules.md
  - Add project-specific rules for new patterns
  - Document common mistakes to avoid
```

### 6. Run relevant agents

```bash
# After implementation, validate:

# If API code changed
"API 보안 체크해줘"

# If UI changed
"UX 리뷰해줘"

# If database queries added
"DB 성능 분석해줘"

# If coordinate logic touched
"좌표 검증해줘"
```

### 7. Write tests (if applicable)
```python
# Add to tests/ directory
# Follow pattern: test_[module_name].py

def test_new_feature():
    # Arrange
    # Act
    # Assert
    pass
```

### 8. Commit
```bash
# Use git workflow from CLAUDE.md
# Include Co-authored-by tag
git add .
git commit -m "feat: add [feature name]

[Brief description]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

## Example: Adding "favorite locations" feature

1. **Clarify**: User wants to save favorite locations
2. **Assess**: Needs new file `backend/saved_locations.py`, modify `app.py` sidebar
3. **Plan**:
   - JSON file for storage
   - Sidebar UI for add/remove
   - Auto-select saved location on startup
4. **Implement**:
   ```python
   # backend/saved_locations.py
   class SavedLocations:
       def save(location): ...
       def load(): ...
       def delete(location): ...

   # app.py
   with st.sidebar:
       saved = SavedLocations.load()
       selected = st.selectbox("저장된 위치", saved)
       if st.button("현재 위치 저장"):
           SavedLocations.save(location)
   ```
5. **Update docs**:
   - PRD.md: Add "FR-5: 즐겨찾기 위치 저장"
   - CLAUDE.md: Mention `saved_locations.json` in architecture
   - README.md: Update "주요 기능" with bullet point
6. **Run**: "UX 리뷰해줘"
7. **Test**: `tests/test_saved_locations.py`
8. **Commit**: `feat: add favorite locations feature`

## Checklist before declaring "done"

- [ ] Feature works as expected
- [ ] Existing features still work
- [ ] All affected docs updated
- [ ] Relevant agents ran successfully
- [ ] Tests written (if applicable)
- [ ] No console errors
- [ ] Committed with proper message

## Common mistakes to avoid

❌ Implementing without understanding existing patterns
❌ Forgetting to update docs
❌ Not running security/UX agents
❌ Creating duplicate functionality
❌ Breaking existing features
