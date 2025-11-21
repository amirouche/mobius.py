# Schema v1 Implementation Strategy

## Executive Summary

This document outlines the strategy for migrating from schema v0 (single JSON file) to schema v1 (directory-based, content-addressed mappings). The migration is a **breaking change** that requires careful planning, backward compatibility, and thorough testing.

**Estimated effort**: 3-5 days of focused development + comprehensive testing

---

## 1. Current State Analysis (Schema v0)

### Storage Structure
```
$OUVERTURE_DIRECTORY/objects/
  XX/
    YYYYYY.json  # Single file contains everything
```

### File Format (v0)
```json
{
  "version": 0,
  "hash": "abc123def456...",
  "normalized_code": "def _ouverture_v_0(...):\n    ...",
  "docstrings": {"eng": "...", "fra": "..."},
  "name_mappings": {"eng": {...}, "fra": {...}},
  "alias_mappings": {"eng": {...}, "fra": {...}}
}
```

### Affected Functions (ouverture.py)

| Function | Lines | Purpose | Modification Needed |
|----------|-------|---------|-------------------|
| `directory_get_ouverture()` | 326-336 | Get ouverture directory | **No change** |
| `hash_compute()` | 321-323 | Compute SHA256 | **Extend** for algorithm support |
| `function_save()` | 339-376 | Save function (v0) | **Major rewrite** |
| `function_load()` | 530-567 | Load function (v0) | **Major rewrite** |
| `function_add()` | 446-486 | CLI add command | **Modify** to use new save |
| `function_get()` | 570-607 | CLI get command | **Modify** to use new load |
| `ast_normalize()` | 272-318 | Normalize AST | **No change** |
| `docstring_replace()` | 489-527 | Replace docstring | **No change** |
| `code_denormalize()` | 378-443 | Denormalize code | **No change** |

**7 functions need modification**, 3 remain unchanged

---

## 2. Target State (Schema v1)

### Storage Structure
```
$OUVERTURE_DIRECTORY/objects/
  ab/
    c123def456.../              # Function directory (full hash as dirname)
      object.json               # Core function data (no language data)
      eng/                      # Language code directory
        xy/
          z789abc.../mapping.json  # Mapping file (full hash as dirname)
        de/
          f012ghi.../mapping.json  # Another variant
      fra-canadian/              # Extended language codes (up to 256 chars)
        mn/
          opqr.../mapping.json
```

### object.json (v1)
```json
{
  "schema_version": 1,
  "hash": "abc123def456...",
  "hash_algorithm": "sha256",
  "normalized_code": "def _ouverture_v_0(...):\n    ...",
  "encoding": "none",
  "metadata": {
    "created": "2025-11-21T10:00:00Z",
    "author": "username",
    "tags": ["math", "statistics"],
    "dependencies": ["def456...", "ghi789..."]
  }
}
```

**Key change**: No `docstrings`, `name_mappings`, or `alias_mappings` in object.json

### mapping.json (v1)
```json
{
  "docstring": "Calculate the average of a list of numbers",
  "name_mapping": {"_ouverture_v_0": "calculate_average", "_ouverture_v_1": "numbers"},
  "alias_mapping": {"abc123": "helper"}
}
```

**Content-addressed**: Hash of this JSON determines the mapping file path

---

## 3. Implementation Phases

### Phase 1: Foundation (Day 1)
**Goal**: Add v1 infrastructure without breaking v0

**New Functions**:
1. `mapping_compute_hash(docstring, name_mapping, alias_mapping) -> str`
   - Create mapping dict, serialize to canonical JSON, compute hash
   - Returns 64-char hex hash

2. `schema_detect_version(func_hash) -> int`
   - Check if function directory exists (v1) or JSON file exists (v0)
   - Returns 0 or 1

3. `metadata_create() -> dict`
   - Generate default metadata (timestamp, author from env, empty tags/deps)

**Modifications**:
- `hash_compute()`: Add optional `algorithm='sha256'` parameter

**Testing**:
- Unit tests for `mapping_compute_hash()` determinism
- Unit tests for `schema_detect_version()` with test fixtures

**Risks**: None (additive changes only)

---

### Phase 2: V1 Write Path (Day 2)
**Goal**: Implement writing v1 format

**New Functions**:
1. `function_save_v1(hash_value, normalized_code, metadata)`
   - Create function directory: `objects/XX/Y.../`
   - Write `object.json` with schema_version=1
   - Does NOT write language data

2. `mapping_save_v1(func_hash, lang, docstring, name_mapping, alias_mapping)`
   - Compute mapping hash
   - Create language directory: `objects/XX/Y.../lang/`
   - Create mapping directory: `objects/XX/Y.../lang/ZZ/W.../`
   - Write `mapping.json`
   - Return mapping hash for confirmation

3. `function_save_dispatch(hash_value, lang, ...)`
   - Wrapper that dispatches to v0 or v1 based on config/env variable
   - Initially always uses v0 (safe)

**Modifications**:
- Keep `function_save()` as v0 implementation (rename to `function_save_v0()`)
- Create new `function_save()` that calls `function_save_dispatch()`

**Testing**:
- Integration test: add function, verify directory structure
- Integration test: add same function in 2 languages, verify deduplication
- Integration test: add same mapping to 2 functions, verify file reuse

**Risks**: Medium (new code paths, but v0 still default)

---

### Phase 3: V1 Read Path (Day 3)
**Goal**: Implement reading v1 format

**New Functions**:
1. `function_load_v1(hash_value) -> dict`
   - Load `object.json`
   - Return dict with normalized_code, metadata, etc.

2. `mappings_list_v1(func_hash, lang) -> List[str]`
   - Scan `objects/XX/Y.../lang/` directory
   - Return list of mapping hashes

3. `mapping_load_v1(func_hash, lang, mapping_hash) -> tuple`
   - Load specific mapping file
   - Return (docstring, name_mapping, alias_mapping)

4. `mapping_get_latest_v1(func_hash, lang) -> str`
   - Get most recently created mapping for language
   - Use filesystem timestamps or metadata field
   - Return mapping hash

5. `function_load_dispatch(hash_value, lang) -> tuple`
   - Detect schema version
   - Call v0 or v1 loader
   - Return unified format: (normalized_code, name_mapping, alias_mapping, docstring, metadata)

**Modifications**:
- Keep `function_load()` as v0 implementation (rename to `function_load_v0()`)
- Create new `function_load()` that calls `function_load_dispatch()`

**Testing**:
- Integration test: write v1, read v1, verify correctness
- Integration test: read v0, verify backward compatibility
- Integration test: list mappings for language
- Integration test: get latest mapping

**Risks**: High (must maintain backward compatibility)

---

### Phase 4: Migration Tool (Day 4)
**Goal**: Provide migration from v0 to v1

**New Functions**:
1. `schema_migrate_function_v0_to_v1(hash_value) -> bool`
   - Load v0 JSON
   - Extract object data and create v1 object.json
   - For each language, create mapping files
   - Optionally delete v0 file or rename to .v0.bak
   - Return success/failure

2. `schema_migrate_all_v0_to_v1(delete_v0=False, dry_run=False)`
   - Scan all v0 files
   - Migrate each function
   - Print statistics (migrated, failed, skipped)
   - Support dry-run mode

3. `schema_validate_v1(func_hash) -> bool`
   - Verify object.json exists and is valid
   - Verify at least one mapping exists
   - Check hash integrity
   - Return validation result

**CLI Commands**:
```bash
ouverture.py migrate               # Migrate all v0 -> v1 (keep v0 files)
ouverture.py migrate --delete-v0   # Migrate and delete v0 files
ouverture.py migrate --dry-run     # Show what would be migrated
ouverture.py migrate HASH          # Migrate specific function
ouverture.py validate              # Validate entire pool
ouverture.py validate HASH         # Validate specific function
```

**Testing**:
- Integration test: migrate simple v0 function
- Integration test: migrate function with multiple languages
- Integration test: migrate function with ouverture imports
- Integration test: dry-run doesn't modify files
- Integration test: validate detects corruption

**Risks**: High (data migration, potential data loss)

**Mitigation**:
- Always backup before migration
- Keep v0 files by default
- Extensive validation after migration

---

### Phase 5: CLI Enhancements (Day 5)
**Goal**: Support v1-specific features in CLI

**Modifications**:
1. `function_add()` - Add `--schema-version` flag (default from config)
2. `function_get()` - Support multiple mappings per language
   ```bash
   ouverture.py get HASH@eng                    # Get latest mapping
   ouverture.py get HASH@eng --list-variants    # List all eng mappings
   ouverture.py get HASH@eng --mapping HASH2    # Get specific mapping
   ```

3. `function_translate()` - NEW command
   ```bash
   ouverture.py translate HASH@eng fra  # Create fra mapping from eng
   ```

4. `function_add()` - Detect and warn about duplicate mappings
   ```bash
   $ ouverture.py add example.py@eng
   Warning: Mapping already exists for this function in 'eng'
   Existing hash: abc123...
   New hash: abc123... (identical)
   Skipping (already stored).
   ```

**Configuration**:
- Add `$OUVERTURE_DIRECTORY/config.json`:
  ```json
  {
    "default_schema_version": 1,
    "author": "username",
    "preferred_languages": ["eng", "fra"]
  }
  ```

**Testing**:
- CLI test: add with v1, verify structure
- CLI test: get with multiple mappings
- CLI test: translate command
- CLI test: duplicate detection

**Risks**: Medium (UX changes)

---

## 4. Backward Compatibility Strategy

### Transition Period (Recommended: 6 months)

**Month 0-1**:
- Release v0.9 with v1 read/write support
- Default: write v0, read both v0 and v1
- Announce migration timeline

**Month 1-3**:
- Users test migration tool
- Report issues, fix bugs
- Default: write v1, read both v0 and v1

**Month 3-6**:
- Encourage migration with warnings
- Add `--force-v0` flag for holdouts
- Document migration in all guides

**Month 6+**:
- Deprecate v0 write support
- Keep v0 read support indefinitely
- Remove v0 write code in v2.0

### Configuration Control

Environment variable: `OUVERTURE_SCHEMA_VERSION`
```bash
export OUVERTURE_SCHEMA_VERSION=0  # Force v0 (legacy)
export OUVERTURE_SCHEMA_VERSION=1  # Force v1 (future)
# Unset: use default from config file or code default
```

### Error Handling

When v0 file encountered:
```
Warning: Function 'abc123...' uses schema v0 (deprecated).
Consider migrating: ouverture.py migrate abc123...
Reading v0 format...
```

---

## 5. Risk Assessment

### High Risk Areas

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Data loss during migration | **CRITICAL** | Low | Backups, keep v0 files, extensive testing |
| Incompatible with existing tools | High | Medium | Maintain v0 read support, document changes |
| Performance degradation | Medium | Low | Benchmark before/after, optimize file I/O |
| Hash collisions in mappings | Medium | Very Low | Use SHA256 (same as function hashes) |
| Language code validation | Low | Medium | Accept any string <256 chars, document conventions |

### Testing Strategy

1. **Unit tests** (50+ tests):
   - All new functions
   - Edge cases (empty mappings, long language codes, special chars)
   - Hash determinism

2. **Integration tests** (20+ tests):
   - Round-trip: add v1 → get v1
   - Backward compat: add v0 → get with v1 code
   - Migration: v0 → v1 → validate
   - Multi-language: same function, 3 languages

3. **Property-based tests** (Hypothesis):
   - Mapping hash determinism
   - Migration preserves data
   - v0 and v1 produce same denormalized output

4. **Manual testing**:
   - Migrate real-world pool (if available)
   - Test with examples in `examples/`
   - Performance testing with 100+ functions

---

## 6. Open Questions & Decisions Needed

### Q1: When to enable v1 by default?
**Options**:
- A) Immediately (aggressive, risky)
- B) After 1 month of testing (balanced)
- C) After user opt-in period (conservative)

**Recommendation**: **B** - Enable v1 by default after 1 month of testing, with easy rollback via env variable.

### Q2: What to do with v0 files after migration?
**Options**:
- A) Delete immediately (clean, but dangerous)
- B) Rename to `.v0.bak` (safe, but clutters)
- C) Keep indefinitely (safest, wastes space)

**Recommendation**: **B** - Rename to `.v0.bak` by default, provide `--delete-v0` flag for cleanup after validation.

### Q3: How to select mapping when multiple exist?
**Options**:
- A) Always use latest (by timestamp)
- B) Let user choose interactively
- C) Use config file to specify preference

**Recommendation**: **A** for `get` command (convenience), **B** with `--interactive` flag for power users.

### Q4: Should mapping hash include timestamp/author?
**Options**:
- A) Yes (every save creates new mapping, no deduplication)
- B) No (identical mappings deduplicated across functions)

**Recommendation**: **B** - Hash only docstring/name_mapping/alias_mapping for maximum deduplication. Store timestamp/author in metadata if needed.

### Q5: Support compression in initial v1 release?
**Options**:
- A) Yes (future-proof, but adds complexity)
- B) No (simpler, add later if needed)

**Recommendation**: **B** - Add `encoding: "none"` field to object.json for future extensibility, but don't implement compression yet. Wait for real-world usage data.

---

## 7. Implementation Checklist

### Phase 1: Foundation
- [ ] Implement `mapping_compute_hash()`
- [ ] Implement `schema_detect_version()`
- [ ] Implement `metadata_create()`
- [ ] Extend `hash_compute()` with algorithm parameter
- [ ] Add unit tests for new functions
- [ ] Update CLAUDE.md with new functions

### Phase 2: V1 Write Path
- [ ] Rename `function_save()` to `function_save_v0()`
- [ ] Implement `function_save_v1()`
- [ ] Implement `mapping_save_v1()`
- [ ] Implement `function_save_dispatch()`
- [ ] Create new `function_save()` wrapper
- [ ] Add integration tests for v1 writing
- [ ] Test deduplication of identical mappings

### Phase 3: V1 Read Path
- [ ] Rename `function_load()` to `function_load_v0()`
- [ ] Implement `function_load_v1()`
- [ ] Implement `mappings_list_v1()`
- [ ] Implement `mapping_load_v1()`
- [ ] Implement `mapping_get_latest_v1()`
- [ ] Implement `function_load_dispatch()`
- [ ] Create new `function_load()` wrapper
- [ ] Add integration tests for v1 reading
- [ ] Test backward compatibility with v0 files

### Phase 4: Migration Tool
- [ ] Implement `schema_migrate_function_v0_to_v1()`
- [ ] Implement `schema_migrate_all_v0_to_v1()`
- [ ] Implement `schema_validate_v1()`
- [ ] Add `migrate` CLI command
- [ ] Add `validate` CLI command
- [ ] Add integration tests for migration
- [ ] Test dry-run mode
- [ ] Create backup mechanism

### Phase 5: CLI Enhancements
- [ ] Add `--schema-version` flag to `add` command
- [ ] Support `--list-variants` in `get` command
- [ ] Support `--mapping HASH` in `get` command
- [ ] Implement `translate` CLI command
- [ ] Add duplicate detection to `add` command
- [ ] Create config file format
- [ ] Add CLI tests for new features
- [ ] Update documentation (README.md, CLAUDE.md)

### Documentation
- [ ] Update TODO.md (mark Priority 0 as completed)
- [ ] Update CLAUDE.md with v1 schema details
- [ ] Create migration guide (MIGRATION_V0_TO_V1.md)
- [ ] Update README.md with v1 examples
- [ ] Add inline code documentation for all new functions
- [ ] Create schema specification document

### Testing
- [ ] 50+ unit tests for new functions
- [ ] 20+ integration tests for v1 workflow
- [ ] 10+ migration tests
- [ ] Property-based tests with Hypothesis
- [ ] Manual testing with examples/
- [ ] Performance benchmarks (v0 vs v1)

---

## 8. Alternatives Considered

### Alternative 1: Hybrid Approach (Single File with References)
**Idea**: Keep single JSON file, but reference external mapping files

```json
{
  "version": 1,
  "hash": "abc123...",
  "normalized_code": "...",
  "mappings": {
    "eng": ["xyz789...", "abc123..."],
    "fra": ["def456..."]
  }
}
```

**Pros**: Easier to implement, less disruptive
**Cons**: Doesn't solve deduplication, mixing concerns

**Decision**: Rejected - Doesn't achieve the goal of content-addressed mappings

### Alternative 2: Database Backend (SQLite)
**Idea**: Store everything in SQLite database instead of filesystem

**Pros**: Easier queries, atomic transactions, better performance
**Cons**: Less git-friendly, harder to inspect, breaks current architecture

**Decision**: Rejected for now - Consider for Priority 2 (remotes)

### Alternative 3: Immediate Breaking Change (No v0 Support)
**Idea**: Remove v0 support entirely, force migration

**Pros**: Simpler code, cleaner architecture
**Cons**: Breaks existing users, no rollback

**Decision**: Rejected - Too aggressive, maintain backward compatibility

---

## 9. Success Criteria

**Phase completion criteria**:
- [ ] All tests pass (unit + integration)
- [ ] No regression in v0 functionality
- [ ] Migration tool successfully migrates all examples
- [ ] Documentation updated
- [ ] Code review approved

**Release criteria**:
- [ ] All phases completed
- [ ] 90%+ test coverage for new code
- [ ] Manual testing on Linux, macOS, Windows
- [ ] Performance: v1 operations within 20% of v0 speed
- [ ] Migration: 100% success rate on test corpus

---

## 10. Timeline

| Phase | Days | Dependencies | Risk |
|-------|------|--------------|------|
| Phase 1: Foundation | 1 | None | Low |
| Phase 2: V1 Write | 1 | Phase 1 | Medium |
| Phase 3: V1 Read | 1 | Phase 2 | High |
| Phase 4: Migration | 1 | Phase 2+3 | High |
| Phase 5: CLI | 1 | Phase 2+3+4 | Medium |
| **Total** | **5 days** | - | - |

**Additional time**:
- Testing & bug fixes: +2 days
- Documentation: +1 day
- Code review & revisions: +1 day

**Total estimated time**: 8-10 days

---

## 11. Next Steps

**Immediate actions**:
1. **Review this strategy** with maintainer/team
2. **Answer open questions** (Q1-Q5 above)
3. **Create feature branch**: `feature/schema-v1`
4. **Start Phase 1** implementation
5. **Set up CI/CD** for automated testing

**Before starting implementation**:
- [ ] Approval on overall strategy
- [ ] Decisions on open questions
- [ ] Agreement on timeline
- [ ] Backup plan for rollback

---

## Conclusion

The migration from schema v0 to v1 is a significant undertaking that will **future-proof** the ouverture storage format. The proposed **5-phase approach** balances:

- **Safety**: Backward compatibility, extensive testing, gradual rollout
- **Flexibility**: Content-addressed mappings, extended language codes, metadata
- **Simplicity**: Clean separation of concerns, discoverable mappings, unified directory structure

**Recommendation**: Proceed with implementation, starting with Phase 1 (Foundation), with close attention to testing and backward compatibility.

The key to success is **incremental progress** with **continuous validation** at each phase.
