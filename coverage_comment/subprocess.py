from __future__ import annotations

import functools
import os
import pathlib
import subprocess
from typing import Any

from coverage_comment import log


class SubProcessError(Exception):
    pass


class GitError(SubProcessError):
    pass


def run(*args, path: pathlib.Path, **kwargs) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=path,
            text=True,
            check=True,
            capture_output=True,
            **kwargs,
        )
        return result.stdout
    except subprocess.CalledProcessError as exc:
        log.info(
            f"Command failed: {args=} {path=} {kwargs=} {exc.stderr=} {exc.returncode=}"
        )
        raise SubProcessError("\n".join([exc.stderr, exc.stdout])) from exc


class Git:
    """
    Wrapper around calling git subprocesses in a way that reads a tiny bit like
    Python code.
    Call a method on git to call the corresponding subcommand (use `_` for `-`).
    Add string parameters for the rest of the command line.

    Returns stdout or raise GitError

    >>> git = Git()
    >>> git.clone(url)
    >>> git.commit("-m", message)
    >>> git.rev_parse("--short", "HEAD")
    """

    cwd = pathlib.Path(".")

    def _git(self, *args: str, env: dict[str, str] | None = None, **kwargs) -> str:
        # When setting the `env` argument to run, instead of inheriting env
        # vars from the current process, the whole environment of the
        # subprocess is whatever we pass. In other words, we can either
        # conditionally pass an `env` parameter, but it's less readable,
        # or we can always pass an `env` parameter, but in this case, we
        # need to always merge `os.environ` to it (and ensure our variables
        # have precedence)
        try:
            return run(
                "git",
                *args,
                path=self.cwd,
                env=os.environ | (env or {}),
                **kwargs,
            )
        except SubProcessError as exc:
            raise GitError from exc

    def __getattr__(self, name: str) -> Any:
        return functools.partial(self._git, name.replace("_", "-"))
