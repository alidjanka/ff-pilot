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
