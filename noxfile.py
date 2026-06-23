import nox
import nox.project
import sys


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    requirements = nox.project.load_toml("pyproject.toml")["project"]["optional-dependencies"]["DEV"]
    if not isinstance(requirements, list):
        raise RuntimeError("expected requirements to be a list")
    if sys.version_info < (3, 12, 0):
        requirements.remove("pyproject")
    session.install(*requirements)
    session.install("-e", ".")
    session.run("ruff", "check")
    session.run("python", "-m", "unittest", "discover")
    if sys.version_info >= (3, 12, 0):
        session.run("pyproject", "check")
