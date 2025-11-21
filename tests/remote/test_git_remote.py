"""
Tests for Git remote functionality.

Tests the Git URL parsing, type detection, and remote operations.
"""
import pytest

import ouverture


def test_remote_type_detect_file():
    """Test detecting file:// remote type"""
    assert ouverture.remote_type_detect("file:///path/to/pool") == "file"


def test_remote_type_detect_git_ssh():
    """Test detecting git SSH remote type"""
    assert ouverture.remote_type_detect("git@github.com:user/repo.git") == "git-ssh"


def test_remote_type_detect_git_https():
    """Test detecting git HTTPS remote type"""
    assert ouverture.remote_type_detect("git+https://github.com/user/repo.git") == "git-https"


def test_remote_type_detect_git_file():
    """Test detecting local git remote type"""
    assert ouverture.remote_type_detect("git+file:///path/to/repo") == "git-file"


def test_remote_type_detect_http():
    """Test detecting HTTP remote type"""
    assert ouverture.remote_type_detect("http://example.com/pool") == "http"


def test_remote_type_detect_https():
    """Test detecting HTTPS remote type"""
    assert ouverture.remote_type_detect("https://example.com/pool") == "https"


def test_remote_type_detect_unknown():
    """Test detecting unknown remote type"""
    assert ouverture.remote_type_detect("ftp://example.com") == "unknown"


def test_git_url_parse_ssh():
    """Test parsing SSH Git URL"""
    result = ouverture.git_url_parse("git@github.com:user/repo.git")

    assert result['protocol'] == 'ssh'
    assert result['host'] == 'github.com'
    assert result['path'] == 'user/repo.git'
    assert result['git_url'] == 'git@github.com:user/repo.git'


def test_git_url_parse_https():
    """Test parsing HTTPS Git URL"""
    result = ouverture.git_url_parse("git+https://github.com/user/repo.git")

    assert result['protocol'] == 'https'
    assert result['host'] == 'github.com'
    assert result['path'] == 'user/repo.git'
    assert result['git_url'] == 'https://github.com/user/repo.git'


def test_git_url_parse_file():
    """Test parsing file Git URL"""
    result = ouverture.git_url_parse("git+file:///home/user/repo")

    assert result['protocol'] == 'file'
    assert result['host'] == ''
    assert result['path'] == '/home/user/repo'
    assert result['git_url'] == 'file:///home/user/repo'


def test_git_url_parse_invalid():
    """Test parsing invalid Git URL raises error"""
    with pytest.raises(ValueError):
        ouverture.git_url_parse("invalid://url")


def test_git_cache_path():
    """Test git cache path generation"""
    path = ouverture.git_cache_path("origin")

    assert "cache" in str(path)
    assert "git" in str(path)
    assert "origin" in str(path)


def test_git_run_version():
    """Test git_run executes git commands"""
    result = ouverture.git_run(['--version'])

    assert result.returncode == 0
    assert 'git version' in result.stdout


def test_git_run_invalid_command():
    """Test git_run handles invalid commands"""
    result = ouverture.git_run(['not-a-real-command'])

    assert result.returncode != 0


def test_git_run_with_cwd(tmp_path):
    """Test git_run with working directory"""
    # Initialize a git repo
    ouverture.git_run(['init'], cwd=str(tmp_path))
    
    # Run status in that directory
    result = ouverture.git_run(['status'], cwd=str(tmp_path))
    
    assert result.returncode == 0
    assert 'On branch' in result.stdout or 'No commits yet' in result.stdout


def test_git_clone_nonexistent_repo(tmp_path):
    """Test git clone with nonexistent repository"""
    local_path = tmp_path / "local_repo"
    git_url = "file:///nonexistent/path/to/repo"

    success = ouverture.git_clone_or_fetch(git_url, local_path)

    assert not success


def test_git_clone_creates_directory(tmp_path):
    """Test git clone creates parent directories"""
    # Create a bare repository
    bare_repo = tmp_path / "bare_repo.git"
    result = ouverture.git_run(['init', '--bare', str(bare_repo)])
    assert result.returncode == 0

    # Clone to nested path that doesn't exist
    local_path = tmp_path / "nested" / "path" / "local_repo"
    git_url = f"file://{bare_repo}"

    success = ouverture.git_clone_or_fetch(git_url, local_path)

    assert success
    assert local_path.exists()
    assert (local_path / ".git").exists()
