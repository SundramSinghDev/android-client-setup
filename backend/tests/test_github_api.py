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


def test_clone_injects_token_for_private_repo():
    from github_api import clone_base_repo
    captured_urls = []
    def fake_run(cmd, **kwargs):
        captured_urls.append(cmd[3])  # url is the 4th arg: git clone --depth=1 <url> <dest>
        return MagicMock(returncode=0, stderr="")
    with patch("github_api.subprocess.run", side_effect=fake_run):
        clone_base_repo("https://github.com/org/private.git", "/tmp/dest", token="MYTOKEN")
    assert captured_urls[0] == "https://MYTOKEN@github.com/org/private.git"


def test_clone_without_token_uses_url_as_is():
    from github_api import clone_base_repo
    captured_urls = []
    def fake_run(cmd, **kwargs):
        captured_urls.append(cmd[3])
        return MagicMock(returncode=0, stderr="")
    with patch("github_api.subprocess.run", side_effect=fake_run):
        clone_base_repo("https://github.com/org/repo.git", "/tmp/dest")
    assert captured_urls[0] == "https://github.com/org/repo.git"


def test_clone_raises_on_failure():
    from github_api import clone_base_repo
    with patch("github_api.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=128, stderr="fatal: not found")
        with pytest.raises(RuntimeError, match="Clone failed"):
            clone_base_repo("https://github.com/org/bad.git", "/tmp/dest")


def test_clone_masks_token_in_error_message():
    from github_api import clone_base_repo
    with patch("github_api.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=128, stderr="fatal: repo not found at https://SECRETTOKEN@github.com/org/repo.git")
        with pytest.raises(RuntimeError) as exc_info:
            clone_base_repo("https://github.com/org/repo.git", "/tmp/dest", token="SECRETTOKEN")
        assert "SECRETTOKEN" not in str(exc_info.value)
        assert "***" in str(exc_info.value)


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


def test_create_github_repo_uses_org():
    from github_api import create_github_repo
    mock_repo = MagicMock()
    mock_repo.clone_url = "https://github.com/org/repo.git"
    mock_org = MagicMock()
    mock_org.create_repo.return_value = mock_repo
    with patch("github_api.Github") as MockGithub:
        MockGithub.return_value.get_organization.return_value = mock_org
        url = create_github_repo("token", "myorg", "myrepo")
    assert url == "https://github.com/org/repo.git"
    mock_org.create_repo.assert_called_once_with("myrepo", private=True, auto_init=False)


def test_create_github_repo_falls_back_to_user_on_404():
    from github import UnknownObjectException
    from github_api import create_github_repo
    mock_repo = MagicMock()
    mock_repo.clone_url = "https://github.com/user/repo.git"
    mock_user = MagicMock()
    mock_user.create_repo.return_value = mock_repo
    with patch("github_api.Github") as MockGithub:
        instance = MockGithub.return_value
        instance.get_organization.side_effect = UnknownObjectException(404, "Not Found", {})
        instance.get_user.return_value = mock_user
        url = create_github_repo("token", "nonexistentorg", "myrepo")
    assert url == "https://github.com/user/repo.git"


def test_create_github_repo_does_not_fallback_on_auth_error():
    from github import GithubException
    from github_api import create_github_repo
    with patch("github_api.Github") as MockGithub:
        instance = MockGithub.return_value
        instance.get_organization.side_effect = GithubException(401, "Unauthorized", {})
        with pytest.raises(GithubException):
            create_github_repo("bad_token", "myorg", "myrepo")
