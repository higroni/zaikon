# Conflict Detection Pipeline Issue

## Problem Description

**Date**: 2026-06-04  
**Pipeline Run ID**: `4ff6d678-0d3a-4e0e-8911-e3fa885b3d70`

### Symptoms
- Draft review created successfully from PDF file
- Pipeline status stuck in `running` for 30+ minutes
- No findings generated
- No artifacts created
- Expected completion time: 1-2 minutes (based on other draft reviews)

### Test Details
- **Document**: `radni_odnosi_0001_000001.pdf`
- **Pages**: 89
- **Characters**: 168,520
- **Corpus**: `7c74a596-2252-499e-a2a8-61c8752a77d2` (235 documents)
- **Text Extraction**: Successful (no OCR needed)

### Comparison with Other Draft Reviews
System has 42 draft reviews total:
- 40 with status `completed` (finished in <1 minute)
- 1 with status `pending`
- 1 with status `running` (our test - stuck for 30+ minutes)

## Root Cause Analysis

### Possible Causes
1. **Pipeline Deadlock**: Process stuck in a specific step
2. **Missing Timeout**: No automatic timeout for pipeline steps
3. **Resource Exhaustion**: Memory or CPU issues
4. **LLM/Embedding Timeout**: Waiting for response that never arrives
5. **Large Document Size**: 89 pages might be too large for current pipeline configuration

### Evidence
- Other draft reviews complete quickly (seconds to 1 minute)
- No error messages in API responses
- Status remains `running` indefinitely
- No progress indicators or intermediate results

## Recommended Solutions

### Immediate Actions
1. **Restart Backend Server**: Kill stuck process and restart
2. **Test with Smaller Document**: Try with 5-10 page document first
3. **Check Backend Logs**: Look for errors, warnings, or stuck operations

### Short-term Fixes
1. **Add Pipeline Timeouts**:
   - Set maximum execution time per step (e.g., 5 minutes)
   - Set maximum total pipeline time (e.g., 10 minutes)
   - Fail gracefully with timeout error

2. **Add Progress Monitoring**:
   - Log each pipeline step completion
   - Update draft review status with current step
   - Store intermediate results

3. **Document Size Limits**:
   - Add validation for maximum document size
   - Split large documents into chunks
   - Process in batches if needed

### Long-term Improvements
1. **Async Pipeline Execution**:
   - Use background task queue (Celery, RQ)
   - Allow cancellation of running pipelines
   - Provide real-time progress updates

2. **Resource Management**:
   - Monitor memory usage per pipeline
   - Implement rate limiting
   - Add circuit breakers for external services

3. **Better Error Handling**:
   - Catch and log all exceptions
   - Provide detailed error messages
   - Allow retry with different parameters

## Testing Strategy

### Test Cases
1. **Small Document** (5-10 pages):
   - Should complete in <1 minute
   - Generate findings if conflicts exist

2. **Medium Document** (20-30 pages):
   - Should complete in 1-3 minutes
   - Test timeout handling

3. **Large Document** (50+ pages):
   - Should either complete or timeout gracefully
   - No indefinite hanging

4. **Stress Test**:
   - Multiple concurrent pipelines
   - Monitor resource usage
   - Verify no deadlocks

## Next Steps

1. ✅ Document the issue
2. ⏳ Restart backend server
3. ⏳ Test with smaller document (10 pages)
4. ⏳ Add timeout configuration
5. ⏳ Implement progress monitoring
6. ⏳ Add document size validation
7. ⏳ Create comprehensive test suite

## Related Files
- Test script: `scripts/test_conflict_detection.py`
- Status checker: `scripts/check_draft_status.py`
- Draft list: `scripts/list_drafts.py`
- API endpoint: `backend/zaikon/api/routers/draft_reviews.py`