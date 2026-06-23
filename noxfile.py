import nox
import nox.project


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    requirements = nox.project.load_toml("pyproject.toml")["project"]["optional-dependencies"]["DEV"]
    session.install(*requirements)
    session.install("-e", ".")
    session.run("ruff", "check")
    session.run("python", "-m", "unittest", "discover")
    session.run("pyproject", "check")
