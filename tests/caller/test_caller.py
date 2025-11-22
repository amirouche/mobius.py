"""
Tests for 'mobius.py caller' command.

Grey-box integration tests for reverse dependency discovery.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


def cli_run(args: list, env: dict = None) -> subprocess.CompletedProcess:
    """Run mobius.py CLI command."""
    cmd = [sys.executable, str(Path(__file__).parent.parent.parent / 'mobius.py')] + args

    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=run_env
    )


def test_caller_invalid_hash_fails(tmp_path):
    """Test that caller fails with invalid hash format"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    result = cli_run(['caller', 'invalid-hash'], env=env)

    assert result.returncode != 0
    assert 'Invalid hash format' in result.stderr


def test_caller_nonexistent_function_fails(tmp_path):
    """Test that caller fails for nonexistent function"""
    mobius_dir = tmp_path / '.mobius'
    (mobius_dir / 'pool').mkdir(parents=True)
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    fake_hash = 'f' * 64
    result = cli_run(['caller', fake_hash], env=env)

    assert result.returncode != 0
    assert 'not found' in result.stderr.lower()


def test_caller_no_callers_succeeds(tmp_path):
    """Test that caller succeeds with no callers found"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    # Setup: Add a function
    test_file = tmp_path / "func.py"
    test_file.write_text('def foo(): return 42')
    add_result = cli_run(['add', f'{test_file}@eng'], env=env)
    func_hash = add_result.stdout.split('Hash:')[1].strip().split()[0]

    # Test
    result = cli_run(['caller', func_hash], env=env)

    # Assert: Should succeed even with no callers
    assert result.returncode == 0


def test_caller_empty_pool_fails(tmp_path):
    """Test that caller handles empty pool"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    fake_hash = 'a' * 64
    result = cli_run(['caller', fake_hash], env=env)

    # Should fail because function doesn't exist
    assert result.returncode != 0
