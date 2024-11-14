from functools import lru_cache
import git
from pathlib import Path
from typing import Any, List

###################################
# GIT Helpers
###################################


def get_commit_tags(repository_folder: Path, commit_hash: str) -> List[str]:
    """
    Get all tags of a commit.
    """
    repo = git.Repo(repository_folder)
    commit = repo.commit(commit_hash)

    return [tag for tag in repo.tags if tag.commit == commit]


@lru_cache
def get_most_recent_tags_before_commit(
    repository_folder: Path, commit_hash: str
) -> List[git.Tag]:
    """
    Get a list of the most recent tags prior to a commit.
    """
    repository = git.Repo(repository_folder)

    for p in repository.iter_commits(commit_hash):
        tags = get_commit_tags(repository_folder, p.hexsha)
        if len(tags) > 0:
            return tags
    return []


@lru_cache
def get_all_commits_in_between(
    repository_folder: Path, most_recent_hash: str, most_ancient_hash: str
) -> List[str]:
    """
    Return a list of commit hashes in between two commit hashes (terminals included).
    """
    repository = git.Repo(repository_folder)
    commits = []
    for p in repository.iter_commits(most_recent_hash):
        commits.append(p.hexsha)
        if p.hexsha == most_ancient_hash:
            break
    return commits


@lru_cache
def get_non_versioned_commits(repository_folder: Path) -> List[str]:
    """
    Get the first sequence of non-versioned commit hashes.

    Start from the HEAD commit up to the first tagged commit (included).
    """
    repository = git.Repo(repository_folder)
    most_recent_tags = get_most_recent_tags_before_commit(
        repository_folder, repository.commit()
    )
    if len(most_recent_tags) == 0:
        return []
    tag = most_recent_tags[-1]
    return get_all_commits_in_between(
        repository_folder, repository.commit(), tag.commit
    )


def get_commit(repository_folder: Path, commit_hash: str) -> git.Commit:
    repository = git.Repo(repository_folder)
    return repository.commit(commit_hash)


def push_new_version(repository_folder: Path, version: str):
    repository = git.Repo(repository_folder)
    tag = repository.create_tag(
        version, repository.commit(), message=f"Release version {version}"
    )
    repository.remote().push(tag)


def get_staging_area(repository_folder: Path) -> List[Any]:
    repository = git.Repo(repository_folder)
    return repository.commit().diff()


def get_versions(repository_path: Path) -> List[str]:
    repo = git.Repo(repository_path)
    return [t.name[1:] for t in repo.tags]


def get_branches_names(repository_path: Path) -> List[str]:
    repo = git.Repo(repository_path)
    return ["/".join(x.name.split("/")[1:]) for x in repo.remote().refs]
