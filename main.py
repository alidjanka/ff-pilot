from RAG.openai_rag import OpenAIRAG

import datetime
import asyncio

from prompts.prompts import Sections
from utils.project_information import create_master_list,retrieve_project

def create_vector_store():
    rag = OpenAIRAG(collection_name="ff-pilot")
    vector_store_id = rag.create_or_retrieve_vector_store()
    print(f"Vector store created: {vector_store_id}")
    file_ids = rag.ingest_files(folder_path='Projekte')
    print("All files are ingested!")
    rag.batch_upload_files(file_ids=file_ids)
    print("Embeddings created!")

def ask():
    rag = OpenAIRAG(collection_name="ff-pilot")
    vector_store_id = rag.create_or_retrieve_vector_store()
    print(f"Vector store created: {vector_store_id}")
    query = '''
    Schreibe Projektbeschreibung und Leistungsumfang mit Einführung in das Projekt, Zielsetzung, Art der Maßnahme und Verweis auf relevante Planungsunterlagen.
    Soll enthalten:
    - Art des Projekts (z. B. Repowering, Neubau)  
    - Standortbeschreibung  
    - Ziel und Umfang  
    - Hinweise auf Planungsunterlagen (Anlagenlayout, PV-Sol, etc.)  
    - Kurzbeschreibung der auszuführenden Arbeiten  
    '''
    answer, file_names = rag.query("Was ist die Anordnung der Module auf dem Satteldach?")
    print(answer)
    print(file_names)

def load_document(doc_path):
    try:
        with open(doc_path, "r") as f:
            full_doc = f.read()
        return full_doc
    except FileNotFoundError:
        return None

async def generate_document(sections):
    rag = OpenAIRAG(collection_name="ff-pilot")
    full_doc = await rag.build_document_text(sections)

    metadata = f"""---
    title: "FLB Dokument"
    date: "{datetime.date.today()}"
    ---

    """

    full_doc_with_metadata = metadata + full_doc
    with open('output/doc.md', "w", encoding="utf-8") as f:
        f.write(full_doc_with_metadata)

async def add_section(new_section_list):
    full_doc = load_document('output/doc.md')
    if full_doc is not None:
        rag = OpenAIRAG(collection_name="ff-pilot")
        new_section = await rag.add_section(new_section_list[0], full_doc)
        with open('output/doc.md', "a", encoding="utf-8") as f:
            f.write('\n\n' + new_section.title + '\n\n' + new_section.content)
    else:
        print("Document could not be found.")

if __name__ == "__main__":
    projects = create_master_list("Projekte/RPS Projekt- und Abrechnungsübersicht.xlsx")
    print(len(projects))  # should be > 1

    for p in projects:
        if p["Bezeichnung & Projektordner"]=="test2":
            print(p)
