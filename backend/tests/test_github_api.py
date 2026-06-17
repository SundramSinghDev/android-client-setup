import subprocess
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_clone_base_repo_calls_git_clone():
    from github_api import clone_base_repo
    with patch("github_api.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        clone_base_repo("https://github.com/org/repo.git", "/tmp/dest")
        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert args[1] == "clone"
        assert "/tmp/dest" in args


def test_clone_raises_on_failure():
    from github_api import clone_base_repo
    with patch("github_api.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=128, stderr="fatal: not found")
        with pytest.raises(RuntimeError, match="Clone failed"):
            clone_base_repo("https://github.com/org/bad.git", "/tmp/dest")


def test_push_to_github_runs_git_sequence():
    from github_api import push_to_github
    with tempfile.TemporaryDirectory() as d:
        with patch("github_api.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            push_to_github(d, "https://github.com/org/repo.git", "TOKEN123")
            commands = [call[0][0][1] for call in mock_run.call_args_list]
            assert "init" in commands
            assert "add" in commands
            assert "commit" in commands
            assert "push" in commands


def test_push_injects_token_into_url():
    from github_api import push_to_github
    captured_urls = []
    with tempfile.TemporaryDirectory() as d:
        def fake_run(cmd, **kwargs):
            if "remote" in cmd:
                captured_urls.append(cmd[-1])
            return MagicMock(returncode=0, stderr="")
        with patch("github_api.subprocess.run", side_effect=fake_run):
            push_to_github(d, "https://github.com/org/repo.git", "MYTOKEN")
    assert any("MYTOKEN@" in url for url in captured_urls)
