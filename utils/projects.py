import json
from pathlib import Path

PROJECT_FILE = Path("data/projects.json")
PROJECT_FILE.parent.mkdir(exist_ok=True)

def load_projects() -> dict:
    if not PROJECT_FILE.exists():
        return {}
    return json.loads(PROJECT_FILE.read_text(encoding="utf-8"))

def save_projects(projects: dict):
    PROJECT_FILE.write_text(
        json.dumps(projects, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

def delete_project(project_id: str) -> bool:
    """
    Delete a project from projects.json by project_id.

    Returns True if the project was deleted,
    False if the project did not exist.
    """
    projects = load_projects()

    if project_id not in projects:
        return False

    del projects[project_id]
    save_projects(projects)

    return True
