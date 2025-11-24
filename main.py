from RAG.openai_rag import OpenAIRAG
import asyncio

from prompts.prompts import create_prompt, sections

def main():
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

async def generate_section():
    rag = OpenAIRAG(collection_name="ff-pilot")
    vector_store_id = rag.create_or_retrieve_vector_store()
    section = '''------------------------------------------------------------
                    Projektbeschreibung und Leistungsumfang
                    ------------------------------------------------------------
                    Include:
                    - project description
                    - address/location
                    - repowering scope
                    - grid connection norms (e.g., VDE-AR-N 4105/4110)
                    - summary of deliverables (planning, installation, commissioning)
                    - options (wallboxes, heat pumps)
                    - what is excluded

                    Style: Overview + enumerated scope of works.'''

    prompt = create_prompt(section)
    result = await rag.generate_section(prompt)
    print(result)

async def run():
    rag = OpenAIRAG(collection_name="ff-pilot")
    full_doc = await rag.build_document_text(sections)
    with open('output/doc.md', "w", encoding="utf-8") as f:
        f.write(full_doc)

if __name__ == "__main__":
    asyncio.run(run())
