# Priority 0 Implementation Strategy

## Executive Summary

This document outlines the strategy for implementing the Priority 0 items from TODO.md. These represent the next wave of critical features after schema v1 completion.

**Priority 0 Items**:
1. **Async/Await Support** - Handle `async def` functions in normalization
2. **Git Remotes** - Git-based remote storage (SSH, HTTPS, local)
3. **Test Reorganization** - Restructure tests by CLI command
4. **Compilation** - Generate standalone executables with PyOxidizer
5. **Applications** - Reference applications (p5py, asyncify, todo-flask)

**Estimated total effort**: 25-35 days

**Recommended order**: Test Reorganization → Async/Await → Git Remotes → Compilation → Applications

---

## 1. Async/Await Support

### Current State

- Only `ast.FunctionDef` is supported
- `async def` functions (`ast.AsyncFunctionDef`) are not recognized
- `await` expressions are not specially handled

### Target State

```python
# Original async function
async def fetch_data(url):
    """Fetch data from URL"""
    response = await http_get(url)
    return response.json()

# Normalized form
async def _ouverture_v_0(_ouverture_v_1):
    """Fetch data from URL"""
    _ouverture_v_2 = await http_get(_ouverture_v_1)
    return _ouverture_v_2.json()
```

### Implementation Phases

#### Phase A1: AST Support (Day 1)
**Goal**: Recognize and process `async def` functions

**Modifications**:
1. `ast_normalize()` - Add `ast.AsyncFunctionDef` handling alongside `ast.FunctionDef`
2. `ASTNormalizer` class - Extend `visit_AsyncFunctionDef()` method
3. `mapping_create_name()` - Handle async function definitions

**Testing**:
- Unit test: Normalize simple async function
- Unit test: Normalize async function with await expressions
- Unit test: Verify hash determinism for async functions

#### Phase A2: CLI Integration (Day 2)
**Goal**: Full CLI support for async functions

**Modifications**:
1. `function_add()` - Accept async functions
2. `function_show()` - Display async functions correctly
3. `code_denormalize()` - Restore async keyword

**Testing**:
- Integration test: Add async function, retrieve it
- Integration test: Same async logic in multiple languages produces same hash

#### Phase A3: Documentation (Day 3)
**Goal**: Document async function behavior

**Deliverables**:
- Update CLAUDE.md with async function handling
- Add async examples to `examples/` directory
- Document limitations (e.g., no async generators initially)

**Risks**: Low - AST module already supports `AsyncFunctionDef`

**Estimated effort**: 3 days

---

## 2. Git Remotes

### Current State

- `file://` remotes implemented (local/network paths)
- No Git repository support
- Remote configuration stored in `$OUVERTURE_DIRECTORY/config.json`

### Target State

```bash
# Git SSH remote
ouverture.py remote add origin git@github.com:user/functions.git
ouverture.py remote pull origin
ouverture.py remote push origin

# Git HTTPS remote
ouverture.py remote add upstream git+https://github.com/org/pool.git

# Local Git remote
ouverture.py remote add local git+file:///path/to/repo
```

### Storage Structure in Git Repository

```
repository/
├── .git/
├── objects/
│   └── sha256/
│       └── ab/
│           └── c123.../
│               ├── object.json
│               └── eng/
│                   └── sha256/
│                       └── xy/
│                           └── z789.../
│                               └── mapping.json
└── README.md
```

### Implementation Phases

#### Phase G1: Git Integration Foundation (Day 1-2)
**Goal**: Basic Git operations

**New Functions**:
1. `git_clone_or_open(remote_url, local_path) -> Repo`
   - Clone if not exists, open if exists
   - Support SSH, HTTPS, and file:// URLs

2. `git_url_parse(url) -> dict`
   - Parse `git@host:user/repo.git` format
   - Parse `git+https://host/user/repo.git` format
   - Parse `git+file:///path/to/repo` format
   - Return: `{protocol, host, path, auth_method}`

3. `remote_type_detect(url) -> str`
   - Detect remote type: `file`, `git-ssh`, `git-https`, `git-file`, `http`, `https`

**Dependencies**:
- `gitpython` library (or `dulwich` for pure Python)

**Testing**:
- Unit test: Parse various Git URL formats
- Unit test: Detect remote type correctly

#### Phase G2: Pull Implementation (Day 3-4)
**Goal**: Fetch functions from Git remotes

**New Functions**:
1. `remote_pull_git(remote_name) -> List[str]`
   - Clone/fetch repository to cache directory
   - Scan for new/updated functions
   - Copy v1 format files to local pool
   - Return list of pulled function hashes

2. `git_cache_path(remote_name) -> Path`
   - Return: `$OUVERTURE_DIRECTORY/cache/git/{remote_name}/`

**Workflow**:
```
git pull/fetch → scan objects/ → compare with local → copy new files
```

**Testing**:
- Integration test: Pull from local Git repository
- Integration test: Pull same function from multiple remotes
- Integration test: Handle merge conflicts (take newest)

#### Phase G3: Push Implementation (Day 5-6)
**Goal**: Publish functions to Git remotes

**New Functions**:
1. `remote_push_git(remote_name, hash_values=None) -> List[str]`
   - Copy function files to cached repository
   - Commit changes with descriptive message
   - Push to remote
   - Return list of pushed function hashes

2. `git_commit_message_generate(hashes) -> str`
   - Generate commit message: "Add functions: abc123..., def456..."

**Workflow**:
```
copy files to cache → git add → git commit → git push
```

**Testing**:
- Integration test: Push to local Git repository
- Integration test: Push specific functions
- Integration test: Handle push conflicts (pull first)

#### Phase G4: Authentication (Day 7)
**Goal**: Support various authentication methods

**Authentication methods**:
1. **SSH keys**: Use system SSH agent or specified key
2. **HTTPS credentials**: Git credential helpers
3. **Token-based**: GitHub/GitLab personal access tokens

**New Functions**:
1. `git_credentials_get(remote_url) -> dict`
   - Query Git credential helper
   - Support `GIT_ASKPASS` environment variable

**Configuration**:
```json
{
  "remotes": {
    "origin": {
      "url": "git@github.com:user/pool.git",
      "auth": {
        "method": "ssh-key",
        "key_path": "~/.ssh/id_ed25519"
      }
    }
  }
}
```

**Testing**:
- Integration test: SSH key authentication
- Integration test: HTTPS with credential helper

#### Phase G5: Conflict Resolution (Day 8)
**Goal**: Handle conflicts gracefully

**Conflict scenarios**:
1. **Same function, different content**: Should never happen (content-addressed)
2. **Same function, new language**: Merge by adding language directory
3. **Same mapping hash**: No conflict (identical content)

**Strategy**: Last-write-wins with warnings

**Testing**:
- Integration test: Concurrent modifications
- Integration test: Conflict detection and warning

**Risks**: Medium - Git operations can be complex

**Estimated effort**: 8 days

---

## 3. Test Reorganization

### Current State

- All tests in `test_ouverture.py` (105+ tests)
- Tests organized by internal function, not by CLI command
- Makes it hard to find tests for specific user-facing features

### Target State

```
tests/
├── conftest.py                 # Shared fixtures
├── test_internals.py           # AST, hash, schema tests
├── add/
│   ├── test_add_simple.py
│   ├── test_add_async.py
│   ├── test_add_multilang.py
│   └── test_add_errors.py
├── show/
│   ├── test_show_single.py
│   ├── test_show_multiple.py
│   └── test_show_v0_compat.py
├── get/
│   └── test_get_basic.py
├── run/
│   ├── test_run_basic.py
│   └── test_run_debug.py
├── translate/
│   └── test_translate_basic.py
├── remote/
│   ├── test_remote_file.py
│   └── test_remote_git.py
├── migrate/
│   └── test_migrate_v0_v1.py
└── integration/
    ├── test_workflow_add_show.py
    └── test_workflow_multilang.py
```

### Implementation Phases

#### Phase T1: Setup Structure (Day 1)
**Goal**: Create directory structure and shared fixtures

**Tasks**:
1. Create `tests/` directory with subdirectories
2. Create `tests/conftest.py` with shared fixtures:
   - `temp_ouverture_dir` - Temporary pool directory
   - `sample_function` - Sample function fixture
   - `normalize_code_for_test` - Helper for normalized code
3. Update `pytest.ini` or `pyproject.toml` for test discovery

#### Phase T2: Migrate Internal Tests (Day 2)
**Goal**: Move internal tests to `test_internals.py`

**Tests to move** (~40 tests):
- AST normalization tests
- Hash computation tests
- Schema detection tests
- Mapping computation tests

**Keep original file temporarily** for comparison

#### Phase T3: Migrate CLI Tests (Day 3-4)
**Goal**: Organize tests by CLI command

**Tests to reorganize**:
- `test_add_*` → `tests/add/`
- `test_show_*` → `tests/show/`
- `test_get_*` → `tests/get/`
- `test_run_*` → `tests/run/`
- `test_translate_*` → `tests/translate/`
- `test_remote_*` → `tests/remote/`
- `test_migrate_*` → `tests/migrate/`

#### Phase T4: Add Integration Tests (Day 5)
**Goal**: Create end-to-end workflow tests

**New tests**:
1. `test_workflow_add_show.py` - Add function, show it, verify output
2. `test_workflow_multilang.py` - Add same function in 3 languages, verify same hash
3. `test_workflow_remote.py` - Add locally, push to remote, pull from remote
4. `test_workflow_migration.py` - Create v0, migrate, verify v1

#### Phase T5: Cleanup (Day 6)
**Goal**: Remove old test file, update documentation

**Tasks**:
1. Delete `test_ouverture.py` after verification
2. Update `README_PYTEST.md` with new structure
3. Update CI/CD configuration

**Risks**: Low - Reorganization only, no logic changes

**Estimated effort**: 6 days

---

## 4. Compilation

### Current State

- Functions can only be executed via `ouverture.py run`
- No standalone distribution mechanism
- Dependencies must be resolved at runtime

### Target State

```bash
# Generate standalone executable
ouverture.py compile abc123...@eng --output ./myapp

# Run the executable
./myapp
# Prompts for function arguments, executes, returns result

# Platform-specific outputs
./myapp           # Linux
./myapp.exe       # Windows
./myapp.app       # macOS (optional)
```

### Implementation Phases

#### Phase C1: Dependency Resolution (Day 1-2)
**Goal**: Resolve all function dependencies transitively

**New Functions**:
1. `dependencies_resolve(func_hash) -> List[str]`
   - Parse ouverture imports from normalized code
   - Recursively resolve dependencies
   - Return topologically sorted list of hashes

2. `dependencies_bundle(hashes, output_dir) -> Path`
   - Copy all function files to output directory
   - Maintain v1 directory structure
   - Return bundle path

**Testing**:
- Unit test: Resolve single dependency
- Unit test: Resolve diamond dependency
- Integration test: Bundle function with 3+ dependencies

#### Phase C2: PyOxidizer Integration (Day 3-5)
**Goal**: Generate standalone executables

**Approach**:
1. Generate PyOxidizer configuration dynamically
2. Create entry point script that:
   - Embeds the bundled functions
   - Prompts for arguments
   - Executes and returns result

**New Functions**:
1. `compile_generate_config(func_hash, lang, output_path) -> str`
   - Generate `pyoxidizer.bzl` configuration
   - Embed function files as resources
   - Configure entry point

2. `compile_build(config_path, output_path) -> Path`
   - Run `pyoxidizer build`
   - Return path to generated executable

**Entry point template**:
```python
#!/usr/bin/env python3
import sys
from ouverture.runtime import execute_function

if __name__ == "__main__":
    result = execute_function("FUNC_HASH", "LANG", sys.argv[1:])
    print(result)
```

**Testing**:
- Integration test: Compile simple function
- Integration test: Compile function with dependencies
- Integration test: Run compiled executable

#### Phase C3: Cross-Platform Support (Day 6-7)
**Goal**: Generate platform-specific binaries

**Platforms**:
1. Linux (x86_64, aarch64)
2. macOS (x86_64, arm64)
3. Windows (x86_64)

**CLI Options**:
```bash
ouverture.py compile HASH@lang --platform linux-x86_64
ouverture.py compile HASH@lang --platform macos-arm64
ouverture.py compile HASH@lang --platform windows-x86_64
ouverture.py compile HASH@lang  # Default: current platform
```

**Testing**:
- Integration test: Compile for current platform
- Manual test: Cross-compilation (requires CI/CD)

#### Phase C4: Documentation (Day 8)
**Goal**: Document compilation workflow

**Deliverables**:
- Add `docs/COMPILATION.md` guide
- Update README.md with compilation examples
- Add troubleshooting section

**Risks**: High - PyOxidizer complexity, cross-platform issues

**Dependencies**:
- PyOxidizer installation
- Rust toolchain (for PyOxidizer)
- Platform-specific SDKs for cross-compilation

**Estimated effort**: 8 days

---

## 5. Applications

### Overview

Reference applications demonstrating ouverture integration:

1. **p5py** - Creative coding library (p5.js port)
2. **asyncify** - Sync-to-async code transformer
3. **todo-flask** - Reference Flask todo application

### p5py Application

**Goal**: Port p5.js creative coding API to Python using ouverture for function sharing

**Scope**:
- Core drawing functions (circle, rect, line, etc.)
- Color management
- Event handling (mouse, keyboard)
- Basic transforms

**Implementation**:
1. Create `examples/p5py/` directory
2. Implement core functions as ouverture-compatible functions
3. Create launcher that loads functions from pool
4. Document usage and examples

**Estimated effort**: 5-7 days

### asyncify Application

**Goal**: Tool for rewriting synchronous Python code to async/await

**Use case**:
```python
# Input (sync)
def fetch_all(urls):
    results = []
    for url in urls:
        response = requests.get(url)
        results.append(response.json())
    return results

# Output (async)
async def fetch_all(urls):
    results = []
    for url in urls:
        response = await aiohttp.get(url)
        results.append(await response.json())
    return results
```

**Implementation**:
1. AST-based transformation
2. Library mapping (requests → aiohttp, etc.)
3. CLI interface: `asyncify input.py output.py`
4. Integration with ouverture (transform functions in pool)

**Estimated effort**: 4-5 days

### todo-flask Application

**Goal**: Reference todo application demonstrating ouverture integration

**Features**:
- CRUD operations for todos
- REST API with Flask
- Functions stored in ouverture pool
- Multilingual support (English, French, Spanish)

**Structure**:
```
examples/todo-flask/
├── app.py              # Flask app (imports from ouverture pool)
├── requirements.txt
├── README.md
└── functions/          # Source functions before adding to pool
    ├── todo_create.py
    ├── todo_read.py
    ├── todo_update.py
    └── todo_delete.py
```

**Estimated effort**: 3-4 days

**Total applications effort**: 12-16 days

---

## 6. Implementation Order

### Recommended Sequence

```
Week 1-2: Test Reorganization (6 days)
    ↓
Week 2-3: Async/Await Support (3 days)
    ↓
Week 3-4: Git Remotes (8 days)
    ↓
Week 5-6: Compilation (8 days)
    ↓
Week 7-9: Applications (12-16 days)
```

### Rationale

1. **Test Reorganization first**: Clean test structure makes subsequent development easier and more confident

2. **Async/Await second**: Small, self-contained feature that unblocks application development (asyncify requires this)

3. **Git Remotes third**: Core infrastructure for sharing functions across teams/projects

4. **Compilation fourth**: Enables distribution of ouverture functions as standalone tools

5. **Applications last**: Demonstrate all features together, serve as integration tests

---

## 7. Risk Assessment

| Feature | Risk Level | Key Risks | Mitigation |
|---------|------------|-----------|------------|
| Async/Await | Low | AST handling edge cases | Comprehensive tests |
| Git Remotes | Medium | Authentication complexity, merge conflicts | Use gitpython, extensive testing |
| Test Reorganization | Low | Test discovery issues | Incremental migration, verify CI |
| Compilation | High | PyOxidizer complexity, cross-platform | Start with single platform, expand |
| Applications | Medium | Scope creep, maintenance burden | Define MVP scope clearly |

---

## 8. Success Criteria

### Per-Feature Criteria

**Async/Await**:
- [ ] All existing tests pass
- [ ] 10+ async-specific tests pass
- [ ] Examples work with async functions

**Git Remotes**:
- [ ] Push/pull works with local Git repo
- [ ] SSH authentication works
- [ ] HTTPS authentication works

**Test Reorganization**:
- [ ] All tests pass in new structure
- [ ] CI/CD updated and green
- [ ] Documentation updated

**Compilation**:
- [ ] Simple function compiles on Linux
- [ ] Compiled executable runs correctly
- [ ] Dependencies resolved transitively

**Applications**:
- [ ] Each application has working demo
- [ ] Documentation complete
- [ ] Examples in pool

### Overall Criteria

- [ ] No regression in existing functionality
- [ ] 90%+ test coverage for new code
- [ ] Documentation updated for all features
- [ ] All examples work end-to-end

---

## 9. Timeline Summary

| Feature | Days | Cumulative |
|---------|------|------------|
| Test Reorganization | 6 | 6 |
| Async/Await | 3 | 9 |
| Git Remotes | 8 | 17 |
| Compilation | 8 | 25 |
| Applications | 12-16 | 37-41 |
| **Buffer/Testing** | +5 | 42-46 |

**Total estimated time**: 6-9 weeks

---

## 10. Next Steps

1. **Review this strategy** - Get approval on scope and approach
2. **Start Test Reorganization** - Low risk, high value
3. **Set up CI/CD** - Ensure tests run on every change
4. **Create feature branches** - One branch per feature
5. **Track progress** - Update checklist as work completes

---

## 11. Dependencies and Prerequisites

### External Dependencies

| Feature | Dependencies | Installation |
|---------|--------------|--------------|
| Async/Await | None | - |
| Git Remotes | `gitpython>=3.1` | `pip install gitpython` |
| Test Reorganization | `pytest>=7.0` | Already installed |
| Compilation | `pyoxidizer>=0.24`, Rust | See PyOxidizer docs |
| p5py | `pygame>=2.0` or `pyglet>=2.0` | `pip install pygame` |
| asyncify | None | - |
| todo-flask | `flask>=2.0` | `pip install flask` |

### Prerequisites

Before starting each feature:

**Git Remotes**:
- [ ] Decide on gitpython vs dulwich
- [ ] Set up test Git repositories (local and remote)
- [ ] Create SSH test keys for CI

**Compilation**:
- [ ] Install PyOxidizer and Rust toolchain
- [ ] Test basic PyOxidizer example
- [ ] Decide on cross-compilation strategy

**Applications**:
- [ ] Define MVP scope for each application
- [ ] Create separate repositories or keep in examples/

---

## Conclusion

Priority 0 represents the next major milestone for Ouverture, transforming it from a local tool to a distributed function sharing platform. The recommended implementation order prioritizes:

1. **Foundation** (Test Reorganization, Async) - Enable confident development
2. **Distribution** (Git Remotes, Compilation) - Enable sharing and deployment
3. **Showcase** (Applications) - Demonstrate value and capabilities

**Key success factors**:
- Incremental implementation with continuous testing
- Clear scope definition to avoid feature creep
- Documentation alongside implementation

**Total effort**: 6-9 weeks for full implementation
