from abc import ABC, abstractmethod
from typing import List

class RAGBase(ABC):

    @abstractmethod
    def ingest_files(self, file_paths: List[str]):
        pass

    @abstractmethod
    def query(self, query: str) -> str:
        pass
