# Plan to Achieve 90% Code Coverage

## Current Status
- **Overall Coverage**: 28%
- **Test Pass Rate**: 97.9% (421/430 tests passing)
- **Problem**: Tests use heavy mocking, so they pass but don't execute actual code

## Coverage by Module (Current)

| Module | Current Coverage | Target | Gap | Priority |
|--------|-----------------|--------|-----|----------|
| api.py | 77% | 90% | +13% | Medium |
| celery_app.py | 100% | 90% | ✅ | Done |
| config.py | 84% | 90% | +6% | Low |
| document_parser.py | 19% | 90% | +71% | HIGH |
| exceptions.py | 100% | 90% | ✅ | Done |
| file_manager.py | 30% | 90% | +60% | HIGH |
| job_manager.py | 34% | 90% | +56% | HIGH |
| layout_analyzer.py | 5% | 90% | +85% | CRITICAL |
| models.py | 100% | 90% | ✅ | Done |
| ocr_engine.py | 25% | 90% | +65% | HIGH |
| pdf_converter.py | 10% | 90% | +80% | CRITICAL |
| redis_client.py | 64% | 90% | +26% | Medium |
| surya_ocr_engine.py | 0% | 90% | +90% | CRITICAL |
| tasks.py | 24% | 90% | +66% | HIGH |
| text_processor.py | 16% | 90% | +74% | HIGH |
| word_generator.py | 16% | 90% | +74% | HIGH |

## Strategy

### Phase 1: Replace Mock-Heavy Tests with Integration Tests (Highest Impact)
**Goal**: Rewrite existing tests to execute real code instead of mocks

**Modules to Fix**:
1. **file_manager.py** (30% → 90%)
   - Current tests mock file operations
   - Solution: Use real temp files/directories in tests
   - Estimated: 15-20 new test cases

2. **job_manager.py** (34% → 90%)
   - Current tests mock Redis heavily
   - Solution: Use fakeredis library for in-memory Redis
   - Estimated: 20-25 new test cases

3. **document_parser.py** (19% → 90%)
   - Current tests mock PDF operations
   - Solution: Create small real PDF fixtures for testing
   - Estimated: 10-15 new test cases

### Phase 2: Critical Missing Coverage (New Tests Required)
**Goal**: Write integration tests for modules with <20% coverage

**Modules to Fix**:
1. **layout_analyzer.py** (5% → 90%)
   - Almost no real code execution
   - Solution: Test with real OCR results, not mocks
   - Estimated: 30-40 new test cases

2. **pdf_converter.py** (10% → 90%)
   - Integration tests failing due to complex mocking
   - Solution: End-to-end tests with real small PDFs
   - Estimated: 15-20 new test cases

3. **surya_ocr_engine.py** (0% → 90%)
   - No tests execute this code
   - Solution: Integration tests with real Surya OCR (or mock at library level, not function level)
   - Estimated: 20-25 new test cases

4. **text_processor.py** (16% → 90%)
   - Minimal coverage
   - Solution: Test all text processing functions with real inputs
   - Estimated: 15-20 new test cases

5. **word_generator.py** (16% → 90%)
   - Minimal coverage
   - Solution: Test Word document generation with real python-docx
   - Estimated: 20-25 new test cases

### Phase 3: High-Value Modules (Good ROI)
**Goal**: Modules with moderate coverage that need boost

**Modules to Fix**:
1. **ocr_engine.py** (25% → 90%)
   - Some coverage but many branches untested
   - Solution: Test all error paths and edge cases
   - Estimated: 15-20 new test cases

2. **tasks.py** (24% → 90%)
   - Celery tasks not fully tested
   - Solution: Test tasks with real dependencies (use fakeredis, temp files)
   - Estimated: 15-20 new test cases

### Phase 4: Polish (Low Effort, High Impact)
**Goal**: Modules close to 90% that need minor additions

**Modules to Fix**:
1. **api.py** (77% → 90%)
   - Missing some error paths
   - Estimated: 5-10 new test cases

2. **config.py** (84% → 90%)
   - Missing environment variable edge cases
   - Estimated: 3-5 new test cases

3. **redis_client.py** (64% → 90%)
   - Missing error handling paths
   - Estimated: 8-10 new test cases

## Implementation Approach

### Test Infrastructure Changes Needed
1. **Add test fixtures**:
   - Small real PDF files (1-2 pages) in `tests/fixtures/`
   - Sample images for OCR testing
   - Sample Word documents for comparison

2. **Add test dependencies**:
   - `fakeredis` - for in-memory Redis testing
   - `pytest-mock` - better mocking utilities
   - Keep existing `pytest`, `hypothesis`, `pytest-cov`

3. **Create test helpers**:
   - `tests/helpers/pdf_fixtures.py` - generate test PDFs
   - `tests/helpers/redis_fixtures.py` - Redis test setup
   - `tests/helpers/file_fixtures.py` - temp file management

### Testing Philosophy Change
**OLD (Current)**:
```python
@patch('app.file_manager.os.path.exists')
def test_file_exists(mock_exists):
    mock_exists.return_value = True
    # Test passes but doesn't execute real code
```

**NEW (Target)**:
```python
def test_file_exists(tmp_path):
    # Create real file
    test_file = tmp_path / "test.pdf"
    test_file.write_bytes(b"content")
    
    # Test with real file operations
    manager = FileManager(str(tmp_path))
    assert manager.file_exists(str(test_file))
```

## Estimated Effort

| Phase | Modules | Test Cases | Estimated Time |
|-------|---------|------------|----------------|
| Phase 1 | 3 modules | 45-60 tests | 3-4 hours |
| Phase 2 | 5 modules | 100-130 tests | 6-8 hours |
| Phase 3 | 2 modules | 30-40 tests | 2-3 hours |
| Phase 4 | 3 modules | 16-25 tests | 1-2 hours |
| **TOTAL** | **13 modules** | **191-255 tests** | **12-17 hours** |

## Risk Assessment

### High Risk Items
1. **Surya OCR Integration** - May be slow/expensive to test
   - Mitigation: Mock at library boundary, not function level
   
2. **PDF Generation** - Creating test PDFs may be complex
   - Mitigation: Use reportlab to generate simple test PDFs

3. **Redis Dependency** - Tests may be flaky
   - Mitigation: Use fakeredis for deterministic testing

### Credit Usage Estimate
- Current conversation: ~110k tokens used
- Estimated for full implementation: 200-300k additional tokens
- **Total estimated**: 310-410k tokens

## Recommendation

### Option A: Full Implementation (Recommended for Production)
- Achieve 90%+ coverage across all modules
- Estimated: 12-17 hours of work
- Credit cost: 200-300k tokens
- Result: Production-ready test suite

### Option B: Phased Approach (Recommended for Budget)
- **Phase 1 only**: Fix 3 critical modules (file_manager, job_manager, document_parser)
- Estimated: 3-4 hours
- Credit cost: 50-70k tokens
- Result: 40-50% overall coverage (not 90%, but better than 28%)

### Option C: Critical Path Only
- Fix only: pdf_converter, layout_analyzer, surya_ocr_engine
- Estimated: 4-5 hours
- Credit cost: 60-80k tokens
- Result: Core conversion pipeline tested, ~50-60% overall coverage

## Next Steps

**Please choose**:
1. **Proceed with Option A** - Full 90% coverage (I'll implement all phases)
2. **Proceed with Option B** - Phase 1 only (quick wins, moderate improvement)
3. **Proceed with Option C** - Critical path only (core functionality)
4. **Stop here** - You'll implement coverage improvements yourself

**If proceeding, I will**:
1. Create test fixtures and helpers first
2. Work module by module, showing coverage improvement after each
3. Run coverage reports frequently to track progress
4. Stop if we hit credit limits you're uncomfortable with

Please let me know which option you prefer, or if you'd like a different approach.
