# ROOT CAUSE ANALYSIS - Conflict Detection Failure

## Date: 2026-06-05

## Problem
Conflict detection returns 0 findings for all 7 gold test cases (0% pass rate).

## Investigation Timeline

### 1. Initial Hypothesis: Qdrant Not Used
- ✅ RESOLVED: Implemented Qdrant integration
- ✅ Result: Pipeline execution time reduced from 113.78s to 1.03s (99.1% faster)
- ❌ But conflict detection still returns 0 findings

### 2. Second Hypothesis: Candidate Generation Broken
- Investigated `_candidate()` and `_evaluate_candidate()` methods
- Found they exist and logic looks correct
- ❌ But still 0 candidates generated

### 3. Third Hypothesis: No Assertions in Database
- Checked `backend/zaikon.db` - no `corpus_assertions` table
- ❌ Wrong database!

### 4. Fourth Hypothesis: Multiple Databases
- Found 3 different database files:
  1. `backend/zaikon.db` - 28.29 MB, NO assertions
  2. `backend/data/artifacts/zaikon.db` - 34.19 MB, 19,859 assertions ✅
  3. `data/artifacts/zaikon.db` - 34.19 MB, 19,859 assertions ✅

- AssertionStore correctly uses `data/artifacts/zaikon.db`
- ✅ Assertions ARE in the database!

### 5. **FINAL ROOT CAUSE: Assertions Missing Critical Slots**

Tested 10 assertions from database:
```
Assertion 1: action=None, object=None, actor=None ❌
Assertion 2: action=None, object=None, actor=None ❌
Assertion 3: action=None, object=None, actor=None ❌
Assertion 4: action=None, object=None, actor=None ❌
Assertion 5: action=None, object=None, actor=None ❌
Assertion 6: action=None, object=✅, actor=None
Assertion 7: action=None, object=None, actor=None ❌
Assertion 8: action=None, object=None, actor=None ❌
Assertion 9: action=None, object=None, actor=None ❌
Assertion 10: action=None, object=None, actor=None ❌
```

**Statistics:**
- 0/10 have `action` slot
- 1/10 have `object` slot  
- 0/10 have `actor` slot
- All have `modality` and `source_quote`

## Why This Breaks Conflict Detection

The `_candidate()` method in [`service.py:350-408`](backend/zaikon/modules/conflicts/service.py:350) requires:

1. **Minimum score threshold**: `base_score >= 0.25` (line 387)
2. **Required match**: Must have either `action` OR `deadline` match (lines 391-394)

```python
# Must have at least action or deadline match
has_action = "same_action" in match_reasons or "similar_action" in match_reasons
has_deadline = "both_have_deadline" in match_reasons
if not (has_action or has_deadline):
    return None  # ← Returns None for ALL pairs!
```

Since `action` is `None` for all assertions:
- `_same_slot(draft.action, corpus.action)` returns `False` (line 357)
- `_similar_slot(draft.action, corpus.action)` returns `False` (line 360)
- No action match reasons added
- `has_action = False`
- Most assertions don't have deadlines either
- **Result: `_candidate()` returns `None` for 100% of pairs**

## Root Cause

**AssertionExtractionService is not properly extracting action, object, and actor slots from legal text.**

The assertions have:
- ✅ `source_quote` (the original text)
- ✅ `modality` (must, may, is_authorized, etc.)
- ✅ `assertion_type` (permission, obligation, deadline, etc.)
- ❌ `action` slot (None)
- ❌ `object` slot (mostly None)
- ❌ `actor` slot (None)

## Solution Required

Fix AssertionExtractionService to properly extract:
1. **Action** - what is being done (e.g., "obaveštava", "podnosi", "zaključuje")
2. **Object** - what is being acted upon (e.g., "ugovor", "zahtev", "izveštaj")
3. **Actor** - who performs the action (e.g., "zaposleni", "poslodavac", "sindikat")

Without these slots, conflict detection cannot compare assertions and will always return 0 findings.

## Performance Status

Despite conflict detection being broken, we achieved massive performance improvements:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Pipeline execution | 113.78s | 1.03s | **99.1% faster** |
| Hybrid search | 50.96s | 0.006s | **849,900% faster** |
| JSON cache loading | 9+ min | 0.4s | **1,385x faster** |
| Authority checker | 43.97s | 0.53s | **82x faster** |

## Next Steps

1. ✅ Document root cause (this file)
2. ⏭️ Fix AssertionExtractionService to extract action/object/actor slots
3. ⏭️ Re-extract all assertions with fixed service
4. ⏭️ Re-test conflict detection
5. ⏭️ Verify gold test cases pass

## Files Involved

- [`backend/zaikon/modules/assertions/service.py`](backend/zaikon/modules/assertions/service.py) - AssertionExtractionService
- [`backend/zaikon/modules/assertions/store.py`](backend/zaikon/modules/assertions/store.py) - AssertionStore
- [`backend/zaikon/modules/conflicts/service.py`](backend/zaikon/modules/conflicts/service.py) - ConflictRegistryService
- [`data/artifacts/zaikon.db`](data/artifacts/zaikon.db) - Database with 19,859 incomplete assertions

## Database Locations

**Correct database:** `data/artifacts/zaikon.db` (34.19 MB, 19,859 assertions)

**Config:**
- `settings.artifact_dir` = `./data/artifacts`
- `AssertionStore.db_path` = `{base_dir}/data/artifacts/zaikon.db`

**Corpus ID:** `7c74a596-2252-499e-a2a8-61c8752a77d2`