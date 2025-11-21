# TODO

This document tracks actionable items for Ouverture development.

Context sources:
- `LIMITS.md` - Current capabilities and known limitations
- `CLAUDE.md` - Technical architecture and development conventions (single-file design)
- `README.md` - Project vision and philosophy

## Completed Items

### Schema v1 Implementation ✅
Complete implementation of the future-proof on-disk schema with content-addressed mappings, multiple language variants, extensible metadata, and migration tools. All 5 implementation phases completed with 105 passing tests.

**Details**: See [strategies/schema-v1.md](strategies/schema-v1.md) for comprehensive implementation strategy and checklist.

**Implemented features**:
- Content-addressed language mappings with deduplication
- Support for multiple mapping variants per language
- Extensible metadata (author, timestamp, tags, dependencies)
- Alternative hash algorithm support (sha256 foundation)
- Schema version detection and backward compatibility
- Migration tool (`ouverture.py migrate`) for v0 → v1
- Validation tool (`ouverture.py validate`) for v1 functions
- Mapping exploration (`ouverture.py show`) with selection menu
- Comment field for mapping variant identification

### User Identity and Configuration ✅
Complete implementation of user configuration system.

**Implemented features**:
- `ouverture.py init` command to initialize ouverture directory (default: `$HOME/.local/ouverture/`)
- `~/.config/ouverture/config.yaml` for user settings (follows XDG Base Directory spec)
- `ouverture.py whoami username [USERNAME]` to set/get username
- `ouverture.py whoami email [EMAIL]` to set/get email
- `ouverture.py whoami public-key [URL]` to set/get public key location
- `ouverture.py whoami language [LANG...]` to set/get preferred languages
- User identity stored in config for attribution

### Remote Repository System (file:// URLs) ✅
Complete implementation of remote repository management for file:// URLs.

**Implemented features**:
- `ouverture.py remote add NAME URL` for file:// remotes
- `ouverture.py remote remove NAME` to remove remotes
- `ouverture.py remote list` to list configured remotes
- `ouverture.py remote pull NAME` to fetch functions from remote
- `ouverture.py remote push NAME` to publish functions to remote
- Remote configuration stored in `~/.config/ouverture/config.yaml`

### Enhanced CLI Commands ✅
Complete implementation of CLI commands for function discovery and operations.

**Implemented features**:
- `ouverture.py log` to show git-like commit log of pool
- `ouverture.py search [QUERY...]` to search and list functions
- `ouverture.py translate HASH@LANG LANG` to add translation to existing function
- `ouverture.py review HASH` to recursively review function and dependencies
- `ouverture.py run HASH@lang` to execute function interactively
- `ouverture.py run HASH@lang --debug` for interactive debugging with native language variables
- `ouverture.py caller HASH` to find functions that depend on a given function
- `ouverture.py refactor WHAT_HASH FROM_HASH TO_HASH` to replace a dependency in a function

## Priority 1: Remote HTTP/HTTPS Support

### HTTP/HTTPS Remotes
- Implement HTTP API client for HTTP/HTTPS remotes
- Add `ouverture.py remote add NAME URL` support for HTTP/HTTPS URLs
- Add authentication/authorization for push operations
- Implement conflict resolution for remote operations
- Add caching layer for remote fetches

### Remote Storage Backends (Advanced)
- Design SQLite schema for local/file-based remotes
- Support multiple remotes with priority/fallback

## Priority 2: Search and Discovery Improvements

### Search Filtering
- Add filtering by language, author, date to `search` command
- Display function statistics (downloads, ratings if available)
- Implement `ouverture.py log [NAME | URL]` to show log of specific remote

### Search Indexing (Performance Enhancement)
- Implement local index for faster search operations
- Index structure: metadata cache (function hashes, docstrings, tags, dependencies)
- Index file: `$OUVERTURE_DIRECTORY/index.db` (SQLite or JSON-based)
- Automatically update index on `add`, `translate`, and `get` operations
- Implement `ouverture.py index rebuild` command to rebuild index from objects directory
- Implement `ouverture.py index verify` command to check index consistency
- Support incremental indexing (only reindex changed functions)
- Search query optimization:
  - Full-text search on docstrings across all languages
  - Prefix/substring matching on function names
  - Tag-based filtering
  - Dependency graph traversal
- Fallback to direct filesystem scan if index is missing or corrupted
- Design considerations:
  - Keep index schema compatible with future v1 storage format
  - Index should be optional (search works without it, just slower)
  - Consider memory-mapped index for large repositories (10,000+ functions)

## Priority 3: Code Quality

### Documentation
- Create `docs/API.md` with Python API documentation
- Create `docs/INTERNALS.md` with architecture guide
- Create `docs/CONTRIBUTING.md` for contributors
- Add docstrings to all public functions
- Document the single-file architecture philosophy in CLAUDE.md

### Packaging
- Create `pyproject.toml` for modern Python packaging
- Add entry point: `ouverture` command
- Test `pip install -e .` works correctly
- Add mypy type checking configuration
- Add ruff linting configuration

## Priority 4: Testing Improvements

### Property-Based Testing
- Implement normalization idempotence tests with Hypothesis
- Implement multilingual equivalence property tests
- Implement roundtrip preservation tests
- Implement hash determinism tests

### Multilingual Test Corpus
- Create `tests/corpus/simple_functions/` with parallel implementations
- Create `tests/corpus/with_imports/` with import examples
- Create `tests/corpus/compositional/` with ouverture imports
- Implement corpus discovery and equivalence testing
- Add test cases in 5+ languages (eng, fra, spa, ara, zho)

### Advanced Testing
- Add fuzzing tests with random AST generation
- Add mutation testing for edge case discovery
- Add performance benchmarks for normalization
- Add performance benchmarks for storage operations
- Add scalability tests with 10,000+ functions
- Add integration tests for CLI workflows

### Regression Testing
- Create snapshot tests for expected normalizations
- Mark known issues with `@pytest.mark.xfail`
- Add regression test suite for bug fixes

## Priority 5: Semantic Understanding

### Short Term (6 months)
- Implement basic pattern matching for top 10 equivalent patterns (sum() vs loop, etc.)
- Add execution-based testing with property tests
- Implement `--semantic-level=basic` flag for optional semantic analysis
- Add warning for possible duplicate functions during `add`

### Medium Term (1 year)
- Expand pattern library to top 100 equivalent patterns
- Implement user feedback system for marking functions as equivalent
- Store equivalence relationships in pool metadata
- Add `ouverture search --similar <hash>` command

### Long Term (2+ years)
- Experiment with ML-based code embeddings (CodeBERT)
- Train semantic equivalence model on collected data
- Implement hybrid syntactic → pattern → execution → ML pipeline
- Add cross-language semantic matching (Python ≡ JavaScript)

## Priority 6: Core Features

### Language Support
- Extend language codes beyond 3 characters to support any string <256 chars
- Add support for async functions (ast.AsyncFunctionDef)
- Document async function behavior and limitations
- Add support for class storage and normalization (if useful)
- Add support for multiple functions per file with dependency tracking

### Type Hints
- Add optional type hint normalization for consistent hashing
- Implement `--normalize-types` flag
- Document impact on multilingual equivalence

### Import Validation
- Implement validation that ouverture imports exist in pool
- Add `--validate-imports` flag to `add` command
- Warn (don't error) when imports are missing

### CLI Improvements
- Add `ouverture list` command to show pool contents
- Add `ouverture list --hash <HASH>` to show languages for hash
- Add `ouverture stats <HASH>` to show function statistics
- Add `--verbose` flag for detailed output
- Add `--version` flag
- Improve error messages with suggestions

## Priority 7: Infrastructure (Microlibrary Vision)

### Phase 1: Centralized Registry (Months 4-6)
- Design HTTP API for function registry
- Implement PostgreSQL schema for metadata
- Implement S3/blob storage for function JSON
- Implement Redis caching layer
- Implement search by hash, signature, description
- Add `ouverture publish` command
- Add `ouverture pull` command from registry
- Create basic web UI for browsing

### Phase 2: Community Features (Months 7-9)
- Implement user accounts and authentication
- Add ratings and reviews system
- Track download statistics
- Create multilingual landing pages
- Implement translation contribution system
- Add reputation system for contributors

### Phase 3: Developer Tools (Months 10-12)
- Create VS Code extension for ouverture
- Implement GitHub Actions integration
- Create pre-commit hooks template
- Build documentation website
- Create example gallery

### Phase 4: Federation (Year 2)
- Design federated registry protocol
- Implement private registry support
- Add registry configuration in `~/.config/ouverture/config.yaml`
- Implement registry priority and fallback
- Add semantic search with ML embeddings

## Priority 8: Research

### Experiments to Run
- Benchmark Top 100 equivalent patterns in real Python codebases
- Measure property testing effectiveness (false positive/negative rates)
- Study user preference for programming styles by language/culture
- Measure performance impact of function composition at depth 10, 100, 1000

### User Studies
- Code comprehension: native language vs English (measure time, bug detection)
- Cultural coding patterns: analyze function structures by language community
- LLM performance: train on multilingual corpus, measure improvement

### Publications
- Publish multilingual function corpus as research dataset
- Write paper on semantic equivalence detection approaches
- Write paper on impact of native-language programming on comprehension
- Write paper on multilingual code sharing infrastructure

## Priority 9: Documentation

### User Documentation
- Document workarounds for unsupported features (classes, globals, etc.)
- Create migration guide for future schema version changes
- Add more examples of compositional functions with ouverture imports
- Create quickstart tutorial
- Create video walkthrough

### Developer Documentation
- Document AST normalization algorithm in detail
- Document hash computation strategy and rationale
- Document storage format and versioning
- Document plugin system design (future)
- Create architecture decision records (ADRs)

## Priority 10: Cross-Language Support

### JavaScript Support
- Implement JavaScript AST normalization
- Map JavaScript constructs to canonical form
- Handle differences in type systems
- Test multilingual equivalence: Python ↔ JavaScript

### Rust Support
- Implement Rust AST normalization (harder due to type system)
- Map Rust constructs to canonical form
- Handle lifetime annotations
- Test multilingual equivalence: Python ↔ Rust

### Universal IR (Long Term)
- Design language-independent intermediate representation
- Map Python, JavaScript, Rust to IR
- Compute hash on IR (true cross-language equivalence)

## Priority 11: Production Readiness

### Security
- Implement static analysis for dangerous patterns (eval, exec, os.system)
- Add sandboxed execution for function testing
- Implement code signing for trusted contributors
- Add malware scanning integration

### Performance
- Profile normalization pipeline for bottlenecks
- Optimize storage format (compression, deduplication)
- Implement caching for frequently accessed functions
- Add lazy loading for metadata

### Reliability
- Add comprehensive error handling throughout codebase
- Implement retries for network operations
- Add circuit breaker for registry access
- Implement graceful degradation

### Monitoring
- Add telemetry for usage tracking (opt-in)
- Implement logging with appropriate levels
- Add health check endpoints for registry
- Create dashboard for pool statistics
