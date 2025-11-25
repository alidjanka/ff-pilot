from RAG.base_rag import RAGBase
from openai import OpenAI
from agents import set_default_openai_key, set_tracing_export_api_key, Agent, FileSearchTool, Runner, trace
from pydantic import BaseModel

from prompts.prompts import create_prompt

from pathlib import Path
from typing import List, Iterator
import os
from dotenv import load_dotenv

load_dotenv()

set_default_openai_key(os.getenv("OPENAI_API_KEY"))
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

class Section(BaseModel):
    title: str
    content: str

class OpenAIRAG(RAGBase):

    def __init__(self, collection_name):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.collection_name = collection_name
        self.model = "gpt-4.1"
        self.vector_store_id = self.create_or_retrieve_vector_store() # might fail
        
    def create_or_retrieve_vector_store(self):
        stores = self.client.vector_stores.list()

        existing_store = next(
            (s for s in stores.data if s.name == self.collection_name),
            None
        )
        if existing_store is None:
            vector_store = self.client.vector_stores.create(
                name=self.collection_name
            )
            self.vector_store = vector_store
            return vector_store.id
        else:
            self.vector_store = existing_store
            return existing_store.id

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
                instructions="You are a document generation agent. You write sections of an FLB document in German only based on the information in the vector store.",
                output_type=Section,
                tools=[
                    FileSearchTool(
                        max_num_results=4,
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

    def build_prompt_with_context(self, section_description: str, previous_sections: List[Section]) -> str:
        context_text = self.build_context(previous_sections) # based on context maybe a different prompt here
        prompt = create_prompt(section_description)
        return f"{context_text}\n\nJetzt schreibe den nächsten Abschnitt:\n{prompt}"


    async def generate_document(self, section_descriptions: List[str]) -> List[Section]:
        """
        Generate a full document, where each section is aware of all previously
        generated sections.
        """
        sections = []

        for p in section_descriptions:
            contextual_prompt = self.build_prompt_with_context(p, sections)
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
        prompt = create_prompt(section_description)
        contextual_prompt = f"Hier ist das vollständige Dokument:{full_doc}\n\nJetzt schreibe einen neuen Abschnitt:\n{prompt}"
        section: Section = await self.generate_section(contextual_prompt)
        #full_doc += '\n\n' + section.title + '\n\n' + section.content
        return section

        
        


