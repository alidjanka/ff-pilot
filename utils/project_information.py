import pandas as pd
import json
from typing import List, Dict, Any

# 4. Convert a row into structured JSON
def row_to_structured_json(row):
    result = {}
    for col, val in row.items():
        if "::" in col:
            group, field = col.split("::", 1)
            result.setdefault(group, {})[field] = val
        else:
            result[col] = val
    return result

def create_master_list(path) -> List[Dict[str, Any]]:
    raw = pd.read_excel(path, header=None)
    # 2. Build hierarchical column names from first two rows
    header_level_1 = raw.iloc[0]
    header_level_2 = raw.iloc[1]

    columns = []
    for h1, h2 in zip(header_level_1, header_level_2):
        if pd.isna(h1):
            columns.append(str(h2))
        else:
            columns.append(f"{h1}::{h2}")

    # 3. Create data frame with proper columns
    df = raw.iloc[2:].copy()
    df.columns = columns

    # 5. Convert all rows
    projects_json = [row_to_structured_json(row) for _, row in df.iterrows()]

    return projects_json

def retrieve_project(projektbezeichnung, projects_json, project_name_field="Bezeichnung & Projektordner"):
    for project in projects_json:
        if project.get(project_name_field) == projektbezeichnung:
            return json.dumps(project, indent=2, ensure_ascii=False, default=str)
    # Only reached if no project matched
    raise ValueError(f"Projekt '{projektbezeichnung}' ist nicht in der Masterliste!")


if __name__ == "__main__":
    # 6. Pretty print JSON (handle dates / NaN safely)
    # 1. Load Excel without headers
    PATH = "data/RPS Projekt- und Abrechnungsübersicht.xlsx"
    projects_json = create_master_list(PATH)
    project = retrieve_project("Lampe", projects_json)
    print(project)
