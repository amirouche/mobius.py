"""
Tests for compilation functionality.

Tests dependency resolution and bundling for function compilation.
"""
import pytest

import ouverture
from tests.conftest import normalize_code_for_test


def test_dependencies_extract_no_deps():
    """Test extracting dependencies from code with no ouverture imports"""
    code = normalize_code_for_test("""
def _ouverture_v_0():
    return 42
""")
    deps = ouverture.dependencies_extract(code)
    assert deps == []


def test_dependencies_extract_single_dep():
    """Test extracting single dependency"""
    code = normalize_code_for_test("""
from ouverture.pool import object_abc123def456789012345678901234567890123456789012345678901234

def _ouverture_v_0():
    return object_abc123def456789012345678901234567890123456789012345678901234._ouverture_v_0()
""")
    deps = ouverture.dependencies_extract(code)
    assert len(deps) == 1
    assert deps[0] == "abc123def456789012345678901234567890123456789012345678901234"


def test_dependencies_extract_multiple_deps():
    """Test extracting multiple dependencies"""
    code = normalize_code_for_test("""
from ouverture.pool import object_abc123def456789012345678901234567890123456789012345678901234
from ouverture.pool import object_def456789012345678901234567890123456789012345678901234abc123

def _ouverture_v_0():
    x = object_abc123def456789012345678901234567890123456789012345678901234._ouverture_v_0()
    y = object_def456789012345678901234567890123456789012345678901234abc123._ouverture_v_0()
    return x + y
""")
    deps = ouverture.dependencies_extract(code)
    assert len(deps) == 2


def test_dependencies_resolve_no_deps(mock_ouverture_dir):
    """Test resolving dependencies for function with no deps"""
    func_hash = "nodeps01" + "0" * 56
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 42")

    ouverture.function_save(func_hash, "eng", normalized_code, "No deps", {"_ouverture_v_0": "answer"}, {})

    deps = ouverture.dependencies_resolve(func_hash)

    assert deps == [func_hash]


def test_dependencies_resolve_single_dep(mock_ouverture_dir):
    """Test resolving single dependency"""
    # Create dependency function
    dep_hash = "helper01" + "0" * 56
    dep_code = normalize_code_for_test("def _ouverture_v_0(): return 10")
    ouverture.function_save(dep_hash, "eng", dep_code, "Helper", {"_ouverture_v_0": "helper"}, {})

    # Create function that depends on it
    main_hash = "main0001" + "0" * 56
    main_code = normalize_code_for_test(f"""
from ouverture.pool import object_{dep_hash}

def _ouverture_v_0():
    return object_{dep_hash}._ouverture_v_0() * 2
""")
    ouverture.function_save(main_hash, "eng", main_code, "Main", {"_ouverture_v_0": "double_helper"}, {dep_hash: "helper"})

    deps = ouverture.dependencies_resolve(main_hash)

    # Should have both hashes, dependency first
    assert len(deps) == 2
    assert deps[0] == dep_hash  # dependency first
    assert deps[1] == main_hash  # main function last


def test_dependencies_resolve_diamond(mock_ouverture_dir):
    """Test resolving diamond dependency pattern"""
    # A depends on B and C
    # B depends on D
    # C depends on D
    # Order should be: D, B, C, A (or D, C, B, A)

    d_hash = "hashd001" + "0" * 56
    d_code = normalize_code_for_test("def _ouverture_v_0(): return 1")
    ouverture.function_save(d_hash, "eng", d_code, "D", {"_ouverture_v_0": "d"}, {})

    b_hash = "hashb001" + "0" * 56
    b_code = normalize_code_for_test(f"""
from ouverture.pool import object_{d_hash}

def _ouverture_v_0():
    return object_{d_hash}._ouverture_v_0() + 1
""")
    ouverture.function_save(b_hash, "eng", b_code, "B", {"_ouverture_v_0": "b"}, {d_hash: "d"})

    c_hash = "hashc001" + "0" * 56
    c_code = normalize_code_for_test(f"""
from ouverture.pool import object_{d_hash}

def _ouverture_v_0():
    return object_{d_hash}._ouverture_v_0() * 2
""")
    ouverture.function_save(c_hash, "eng", c_code, "C", {"_ouverture_v_0": "c"}, {d_hash: "d"})

    a_hash = "hasha001" + "0" * 56
    a_code = normalize_code_for_test(f"""
from ouverture.pool import object_{b_hash}
from ouverture.pool import object_{c_hash}

def _ouverture_v_0():
    return object_{b_hash}._ouverture_v_0() + object_{c_hash}._ouverture_v_0()
""")
    ouverture.function_save(a_hash, "eng", a_code, "A", {"_ouverture_v_0": "a"}, {b_hash: "b", c_hash: "c"})

    deps = ouverture.dependencies_resolve(a_hash)

    # Should have all 4 hashes
    assert len(deps) == 4
    # D should come before B and C
    assert deps.index(d_hash) < deps.index(b_hash)
    assert deps.index(d_hash) < deps.index(c_hash)
    # A should be last
    assert deps[-1] == a_hash


def test_dependencies_bundle(mock_ouverture_dir, tmp_path):
    """Test bundling functions to output directory"""
    func_hash = "bundle01" + "0" * 56
    normalized_code = normalize_code_for_test("def _ouverture_v_0(): return 99")
    ouverture.function_save(func_hash, "eng", normalized_code, "Bundle test", {"_ouverture_v_0": "test"}, {})

    output_dir = tmp_path / "bundle_output"
    result = ouverture.dependencies_bundle([func_hash], output_dir)

    assert result == output_dir
    assert output_dir.exists()
    assert (output_dir / "objects").exists()


def test_compile_generate_config():
    """Test generating PyOxidizer configuration"""
    config = ouverture.compile_generate_config("abc123" + "0" * 58, "eng", "myapp")

    assert "PyOxidizer configuration" in config
    assert "myapp" in config
    assert "abc123" in config
    assert "eng" in config


def test_compile_generate_runtime(tmp_path):
    """Test generating runtime module"""
    func_hash = "runtime1" + "0" * 56
    runtime_dir = ouverture.compile_generate_runtime(func_hash, "eng", tmp_path)

    assert runtime_dir.exists()
    assert (runtime_dir / "__init__.py").exists()

    # Read and verify content
    init_content = (runtime_dir / "__init__.py").read_text()
    assert "execute_function" in init_content
    assert "function_load" in init_content
    assert "code_denormalize" in init_content
