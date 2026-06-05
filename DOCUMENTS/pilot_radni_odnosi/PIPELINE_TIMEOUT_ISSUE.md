# Pipeline Timeout Issue - Critical Performance Problem

**Date**: 2026-06-05  
**Status**: 🔴 CRITICAL - Pipeline unusably slow

## Problem Summary

The draft review pipeline is **extremely slow** - even a tiny 760-byte document takes over 2 minutes and still hasn't completed. Large PDFs (89 pages) timeout after 10 minutes with no completion.

## Evidence

### Test 1: Large PDF (89 pages, ~531 KB)
- **File**: `radni_odnosi_0001_000001.pdf`
- **Draft ID**: `45bdd7d3-21ad-4c71-bf42-cec1db2b937c`
- **Result**: Timeout after 10 minutes
- **Status**: `running` (still processing after timeout)
- **Findings**: 0

### Test 2: Small Text File (760 bytes)
- **File**: `test_small.txt`
- **Draft ID**: `a4acd1d0-87dd-44d2-a5c3-808d22b4477f`
- **Result**: Timeout after 2 minutes
- **Status**: `running` (still processing)
- **Findings**: 0

## Root Cause Analysis

### 1. **Synchronous Pipeline Execution**
The `/run` endpoint executes the entire pipeline **synchronously**:
- No background task/threading
- HTTP request blocks until pipeline completes
- Client timeout doesn't stop server-side processing

**Location**: `backend/zaikon/modules/draft_reviews/service.py:246-400`

```python
def run_draft_review(self, pipeline_run_id: UUID) -> RunDraftReviewResponse:
    # Sets status to "running"
    record.status = JobStatus.running
    
    # Then executes entire pipeline synchronously
    # Step 1: Load content
    # Step 2: Normalize text
    # Step 3: Classify document
    # ... (10+ steps)
    # All blocking!
```

### 2. **Performance Bottleneck - Unknown Step**
We don't know which step is slow because:
- Pipeline is still running (can't see timing logs)
- No intermediate progress reporting
- Logs only show step completion, not in-progress status

### 3. **Previous Performance Data**
From earlier tests with cached data:
- **Total time**: 18.1s for small document
- **Slowest steps**:
  - Extract corpus assertions: 8.47s (46.8%)
  - Load corpus documents: 4.82s (26.6%)
  - Evaluate conflicts: 2.03s (11.2%)

**But current test is 10x slower!** Something changed or broke.

## Hypothesis

### Most Likely: Qdrant Connection Issue
The embedded Qdrant might be:
1. **Not responding** - causing long timeouts on each query
2. **Very slow** - database performance degraded
3. **Deadlocked** - waiting for resources

### Evidence:
- Corpus loading involves Qdrant queries
- Assertion extraction may use Qdrant for similarity search
- Previous tests worked with cached data (no Qdrant queries)

## Immediate Actions Needed

### 1. Check Backend Logs
Look for:
- Qdrant connection errors
- Timeout warnings
- Which step is currently executing

### 2. Test Qdrant Directly
```python
# Quick Qdrant health check
from qdrant_client import QdrantClient
client = QdrantClient(path="./data/qdrant_storage")
collections = client.get_collections()
print(collections)
```

### 3. Add Progress Logging
Modify `run_draft_review` to log:
- Start of each step
- Not just completion

### 4. Implement Async Pipeline
Convert to background task:
```python
@router.post("/{pipeline_run_id}/run")
async def run_draft_review(pipeline_run_id: UUID):
    # Start background task
    background_tasks.add_task(
        get_draft_review_service().run_draft_review,
        pipeline_run_id
    )
    return {"status": "started"}
```

## Next Steps

1. ✅ Document issue (this file)
2. ⏳ Check backend server logs for errors
3. ⏳ Test Qdrant connection directly
4. ⏳ Add detailed step-by-step logging
5. ⏳ Identify bottleneck step
6. ⏳ Fix performance issue
7. ⏳ Implement async pipeline execution
8. ⏳ Re-test with real PDFs

## Impact

**CRITICAL** - System is currently unusable for:
- Real document analysis (large PDFs)
- Production use
- Demo purposes

Even small test documents take too long to be practical.

## Timeline

- **Discovered**: 2026-06-05 07:00 UTC
- **First test**: Large PDF timeout (10 min)
- **Second test**: Small file timeout (2 min)
- **Status**: Under investigation

---

**Priority**: 🔴 P0 - Blocking all draft review functionality