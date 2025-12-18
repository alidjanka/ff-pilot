from RAG.base_rag import RAGBase
from openai import OpenAI
from agents import set_default_openai_key, set_tracing_export_api_key, Agent, FileSearchTool, Runner, trace
from pydantic import BaseModel

from prompts.prompts import create_prompt
from prompts.prompts_v2 import create_prompt_v2, create_prompt_v3
from pathlib import Path
from typing import List, Iterator
import time
import os
from dotenv import load_dotenv

import streamlit as st

load_dotenv()

set_default_openai_key(st.secrets["openai"]["OPENAI_API_KEY"])
set_tracing_export_api_key(st.secrets["openai"]["OPENAI_API_KEY"])

class Section(BaseModel):
    title: str
    content: str

class UpdatedDocument(BaseModel):
    content: str

class OpenAIRAG(RAGBase):

    def __init__(self, projektbezeichnung="", objektadresse="", ansprechpartner=""):
        #self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
        self.projektbezeichnung = projektbezeichnung
        self.objektadresse = objektadresse
        self.ansprechpartner = ansprechpartner
        self.model = "gpt-4.1"
        if len(projektbezeichnung)>1:
            self.vector_store_id = self.create_or_retrieve_vector_store()

    def list_project_names(self):
        vector_stores = []
        projects = {}
        cursor = None

        while True:
            response = self.client.vector_stores.list(after=cursor, limit=100)
            vector_stores.extend(response.data)

            if not response.has_more:
                break
            cursor = response.data[-1].id

        for vs in vector_stores:
            print(vs.name, vs.id)
            projects[vs.name] = vs.id
        return projects
        
    def create_or_retrieve_vector_store(self):
        stores = self.client.vector_stores.list()

        existing_store = next(
            (s for s in stores.data if s.name == self.projektbezeichnung),
            None
        )
        if existing_store is None:
            vector_store = self.client.vector_stores.create(
                name=self.projektbezeichnung
            )
            self.vector_store = vector_store
            return vector_store.id
        else:
            self.vector_store = existing_store
            return existing_store.id
    
    def delete_vector_store(self, max_retries=3, delay=2):
        """
        Deletes the vector store along with its files, retrying if any step fails.
        
        Args:
            max_retries (int): Maximum number of retry attempts.
            delay (float): Delay in seconds between retries.
        
        Returns:
            bool: True if deletion succeeded, False otherwise.
        """
        attempt = 0
        while attempt < max_retries:
            try:
                # 1. List files in the vector store
                files = self.client.vector_stores.files.list(
                    vector_store_id=self.vector_store_id
                )

                # 2. Delete each file
                for f in files.data:
                    try:
                        self.client.vector_stores.files.delete(
                            vector_store_id=self.vector_store_id,
                            file_id=f.id
                        )
                    except Exception as file_err:
                        time.sleep(delay)
                        try:
                            self.client.vector_stores.files.delete(
                                vector_store_id=self.vector_store_id,
                                file_id=f.id
                            )
                        except Exception as file_err:
                            print(f"Warning: failed to delete file {f.id}: {file_err}")
                    try:
                        self.client.files.delete(f.id)
                    except Exception as file_err:
                        print(f"Warning: failed to delete global file {f.id}: {file_err}")
                        time.sleep(delay)
                        try:
                            self.client.files.delete(f.id)
                        except Exception as file_err:
                            print(f"Warning: failed to delete global file {f.id}: {file_err}")
                # 3. Delete the vector store
                self.client.vector_stores.delete(
                    vector_store_id=self.vector_store_id
                )

                # If we reach here, everything succeeded
                return True

            except Exception as e:
                attempt += 1
                print(f"Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    print("All retry attempts failed.")
                    return False


    def delete_file(self, file_id: str, max_retries: int = 3, delay: float = 2):
        """
        Deletes a file from the vector store and optionally permanently, with retries.
        
        Args:
            file_id (str): ID of the file to delete.
            max_retries (int): Maximum number of retry attempts.
            delay (float): Delay in seconds between retries.
        """
        attempt = 0
        while attempt < max_retries:
            try:
                # Remove file from vector store
                self.client.vector_stores.files.delete(
                    vector_store_id=self.vector_store_id,
                    file_id=file_id
                )

                # OPTIONAL: permanently delete file
                self.client.files.delete(file_id)
                
                #return True  # Success

            except Exception as e:
                attempt += 1
                print(f"Attempt {attempt}/{max_retries} failed for file {file_id}: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    print(f"Failed to delete file {file_id} after {max_retries} attempts.")
                    #return False


    def list_files(self):
        return self.client.vector_stores.files.list(vector_store_id=self.vector_store_id)

    def retrieve_filename(self, file_id):   
        file_obj = self.client.files.retrieve(file_id)
        return file_obj.filename

    def ingest_file(self, file_path):
        if file_path.suffix.lower() == ".pdf":
            # Handle local file path
            with open(file_path, "rb") as file_content:
                result = self.client.files.create(
                    file=file_content,
                    purpose="assistants"
                )
            return result.id
        else:
            return None

    def get_all_files(folder_path: str) -> List[Path]:
        """
        Recursively collect all files inside the given folder.
        Returns a list of Path objects.
        """
        base = Path(folder_path)
        if not base.exists() or not base.is_dir():
            raise ValueError(f"Folder does not exist: {folder_path}")

        # rglob("*") gives everything; we filter only files
        return [p for p in base.rglob("*") if p.is_file()]


    def walk_folder(self, folder_path: str, exclude_folders: List[str] = None) -> Iterator[Path]:
        """
        Recursively yield file paths in `folder_path`,
        skipping any folder whose name is in `exclude_folders`.
        """
        exclude_folders = set(exclude_folders or [])

        for root, dirnames, filenames in os.walk(folder_path):
            # Remove excluded folders from dirnames so os.walk won't recurse into them
            dirnames[:] = [d for d in dirnames if d not in exclude_folders]

            for filename in filenames:
                yield Path(root) / filename

    def ingest_files(self, folder_path):
        file_ids = []
        # call openai ingestion
        for file in self.walk_folder(folder_path=folder_path, exclude_folders=["ALT"]):
            file_id = self.ingest_file(file)
            if file_id is not None:
                file_ids.append(file_id)
            else:
                print(f"File {file} not ingested")
        return file_ids

    def batch_upload_files(self, file_ids):
        self.client.vector_stores.file_batches.create_and_poll(
            vector_store_id=self.vector_store.id,
            file_ids=file_ids
        )
        
### This part is compatible with streamlit
    def ingest_uploaded_file(self, uploaded_file):
        """
        Ingest a Streamlit UploadedFile and attach project metadata
        """
        file_obj = self.client.files.create(
            file=uploaded_file,
            purpose="assistants"
        )

        self.client.vector_stores.files.create(
            vector_store_id=self.vector_store_id,
            file_id=file_obj.id,
        )

        return file_obj.id

    def search(self, query: str):
        return self.client.vector_stores.search(
            vector_store_id=self.vector_store_id,
            query=query,
        )

    def query(self, query: str):
        response = self.client.responses.create(
            model=self.model,
            input=query,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [self.vector_store.id]
            }]
        )

        # There should be one main assistant message with the synthesized answer
        answer_text = ""
        cited_files = []
        file_names = []

        for item in response.output:
            if getattr(item, "type", None) == "message":
                # Usually there's only one message with the synthesized answer
                block = item.content[0]  # first (and typically only) content block
                answer_text = block.text

                # Collect all file citations
                if hasattr(block, "annotations") and block.annotations:
                    for annotation in block.annotations:
                        if annotation.type == "file_citation":
                            cited_files.append({
                                "filename": annotation.filename,
                                "file_id": annotation.file_id,
                                "index": getattr(annotation, "index", None)
                            })
                            file_names.append(annotation.filename)
                break  # stop after the first assistant message

        return answer_text, file_names

    async def generate_section(self, prompt):
        file_search_agent = Agent(
                name="File searcher",
                instructions="You are a document generation agent.",
                output_type=Section,
                tools=[
                    FileSearchTool(
                        max_num_results=5,
                        vector_store_ids=[self.vector_store.id],
                        include_search_results=True,
                    )
                ],
            )  

        result = await Runner.run(file_search_agent, prompt)
        return result.final_output

    def build_context(self, sections: List[Section]) -> str:
        if not sections:
            return ""

        context = "Dies sind die bisher erstellten Dokumentabschnitte:\n\n"
        for sec in sections:
            context += f"### {sec.title}\n{sec.content}\n\n"
        return context

    def build_prompt_with_context(self, section_description: str, previous_sections: List[Section], projektbezeichnung: str) -> str:
        context_text = self.build_context(previous_sections) # based on context maybe a different prompt here
        prompt = create_prompt_v3(section_description, projektbezeichnung)
        if len(context_text) == 0:
            return prompt
        else:
            return f"{context_text}Jetzt schreibe den nächsten Abschnitt:\n{prompt}"

    async def generate_document(self, section_descriptions: List[str], projektbezeichnung: str) -> List[Section]:
        """
        Generate a full document, where each section is aware of all previously
        generated sections.
        """
        sections = []

        for p in section_descriptions:
            contextual_prompt = self.build_prompt_with_context(p, sections, projektbezeichnung)
            section: Section = await self.generate_section(contextual_prompt)
            sections.append(section)

        return sections

    async def build_document_text(self, prompts: List[str]) -> str:
        sections = await self.generate_document(prompts)

        full_doc = ""
        for sec in sections:
            full_doc += f"# {sec.title}\n\n{sec.content}\n\n"

        return full_doc

    async def add_section(self, section_description: str, full_doc: str):
        prompt = create_prompt_v2(section_description)
        contextual_prompt = f"Hier ist das vollständige Dokument:{full_doc}\n\nJetzt schreibe einen neuen Abschnitt:\n{prompt}"
        section: Section = await self.generate_section(contextual_prompt)
        #full_doc += '\n\n' + section.title + '\n\n' + section.content
        return section

    async def update_document(self, prompt: str, full_doc: str):
        document_update_agent = Agent(
                name="Document Updater",
                instructions="You are a document generation agent. Based on the provided document and user prompt, you update the document. Keep the structure same only change the content based on user query. Return the updated document in German.",
                output_type=UpdatedDocument,
                tools=[
                    FileSearchTool(
                        max_num_results=4,
                        vector_store_ids=[self.vector_store.id],
                        include_search_results=True,
                    )
                ],
            )  

        result = await Runner.run(document_update_agent, prompt)
        return result.final_output        

        
        


