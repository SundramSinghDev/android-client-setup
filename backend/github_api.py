import subprocess
from github import Github, GithubException, UnknownObjectException


def clone_base_repo(repo_url: str, dest_dir: str, token: str | None = None) -> None:
    """Clone the base Android repo (shallow) into dest_dir."""
    if token and repo_url.startswith("https://"):
        auth_url = repo_url.replace("https://", f"https://{token}@")
    else:
        auth_url = repo_url
    result = subprocess.run(
        ["git", "clone", "--depth=1", auth_url, dest_dir],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        safe_stderr = result.stderr.replace(token, "***") if token else result.stderr
        raise RuntimeError(f"Clone failed: {safe_stderr}")


def create_github_repo(token: str, org: str, repo_name: str) -> str:
    """
    Create a new private GitHub repo named repo_name under org (or user).
    Returns the HTTPS clone URL.
    """
    g = Github(token)
    try:
        owner = g.get_organization(org)
    except UnknownObjectException:
        owner = g.get_user()
    try:
        repo = owner.create_repo(repo_name, private=True, auto_init=False)
    except GithubException as e:
        if e.status == 422 and any(
            err.get("message") == "name already exists on this account"
            for err in (e.data.get("errors") or [])
        ):
            raise RuntimeError(
                f"A GitHub repository named '{repo_name}' already exists on this account. "
                f"Use a different Project Name or Merchant ID."
            ) from None
        raise
    return repo.clone_url


def push_to_github(project_dir: str, repo_url: str, token: str) -> None:
    """
    Initialise a git repo in project_dir, commit everything,
    and push to the newly created GitHub repo.
    Token is injected into the HTTPS URL for auth.
    """
    auth_url = repo_url.replace("https://", f"https://{token}@")
    commands = [
        ["git", "init"],
        ["git", "add", "."],
        ["git", "commit", "-m", "feat: initial client project setup"],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "set-url", "origin", auth_url],
        ["git", "push", "-u", "origin", "main"],
    ]
    for cmd in commands:
        result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if result.returncode != 0:
            safe_stderr = result.stderr.replace(token, "***")
            raise RuntimeError(f"`git {cmd[1]}` failed: {safe_stderr}")
