"""
Tests for 'mobius.py validate' command.

Grey-box integration tests for function validation.
"""
import json
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


def test_validate_valid_function(tmp_path):
    """Test that validate succeeds for valid function"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    # Setup: Add a function
    test_file = tmp_path / "func.py"
    test_file.write_text('def foo(): pass')
    add_result = cli_run(['add', f'{test_file}@eng'], env=env)
    func_hash = add_result.stdout.split('Hash:')[1].strip().split()[0]

    # Test
    result = cli_run(['validate', func_hash], env=env)

    # Assert
    assert result.returncode == 0
    assert 'valid' in result.stdout.lower()


def test_validate_nonexistent_function_fails(tmp_path):
    """Test that validate fails for nonexistent function"""
    mobius_dir = tmp_path / '.mobius'
    (mobius_dir / 'pool').mkdir(parents=True)
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    fake_hash = 'f' * 64
    result = cli_run(['validate', fake_hash], env=env)

    assert result.returncode != 0
    assert 'invalid' in result.stderr.lower()
    assert 'object.json not found' in result.stderr


def test_validate_corrupted_object_json_fails(tmp_path):
    """Test that validate fails for corrupted object.json"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    # Setup: Create corrupted function
    fake_hash = 'a' * 64
    func_dir = mobius_dir / 'pool' / fake_hash[:2] / fake_hash[2:]
    func_dir.mkdir(parents=True)
    (func_dir / 'object.json').write_text('not valid json')

    # Test
    result = cli_run(['validate', fake_hash], env=env)

    # Assert
    assert result.returncode != 0
    assert 'invalid' in result.stderr.lower()


def test_validate_missing_fields_fails(tmp_path):
    """Test that validate fails when required fields are missing"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    # Setup: Create function with incomplete object.json
    fake_hash = 'b' * 64
    func_dir = mobius_dir / 'pool' / fake_hash[:2] / fake_hash[2:]
    func_dir.mkdir(parents=True)
    (func_dir / 'object.json').write_text(json.dumps({
        'schema_version': 1,
        'hash': fake_hash
        # Missing: normalized_code, metadata
    }))

    # Test
    result = cli_run(['validate', fake_hash], env=env)

    # Assert
    assert result.returncode != 0
    assert 'invalid' in result.stderr.lower()
    assert 'Missing required field' in result.stderr


def test_validate_wrong_schema_version_fails(tmp_path):
    """Test that validate fails for wrong schema version"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    # Setup: Create function with wrong schema version
    fake_hash = 'c' * 64
    func_dir = mobius_dir / 'pool' / fake_hash[:2] / fake_hash[2:]
    func_dir.mkdir(parents=True)
    (func_dir / 'object.json').write_text(json.dumps({
        'schema_version': 99,
        'hash': fake_hash,
        'normalized_code': 'def _mobius_v_0(): pass',
        'metadata': {}
    }))

    # Test
    result = cli_run(['validate', fake_hash], env=env)

    # Assert
    assert result.returncode != 0
    assert 'Invalid schema version' in result.stderr


def test_validate_no_language_mapping_fails(tmp_path):
    """Test that validate fails when no language mapping exists"""
    mobius_dir = tmp_path / '.mobius'
    env = {'MOBIUS_DIRECTORY': str(mobius_dir)}

    # Setup: Create function without language mapping
    fake_hash = 'd' * 64
    func_dir = mobius_dir / 'pool' / fake_hash[:2] / fake_hash[2:]
    func_dir.mkdir(parents=True)
    (func_dir / 'object.json').write_text(json.dumps({
        'schema_version': 1,
        'hash': fake_hash,
        'normalized_code': 'def _mobius_v_0(): pass',
        'metadata': {'created': '2025-01-01', 'name': 'test', 'email': 'test@example.com'}
    }))

    # Test
    result = cli_run(['validate', fake_hash], env=env)

    # Assert
    assert result.returncode != 0
    assert 'No language mappings found' in result.stderr
