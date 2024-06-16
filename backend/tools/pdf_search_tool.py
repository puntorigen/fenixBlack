from typing import Any, Optional, Type

from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel, Field

from crewai_tools import BaseTool
#from ..rag.rag_tool import RagTool

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


class FixedPDFSearchToolSchema(BaseModel):
    """Input for PDFSearchTool."""

    query: str = Field(
        ..., description="Mandatory query you want to use to search the PDF's content"
    )


class PDFSearchToolSchema(FixedPDFSearchToolSchema):
    """Input for PDFSearchTool."""

    pdf: str = Field(..., description="Mandatory pdf path you want to search")


class PDFSearchTool(BaseTool):
    name: str = "Search a PDF's content"
    description: str = "A tool that can be used to semantic search a query from a PDF's content."
    args_schema: Type[BaseModel] = PDFSearchToolSchema

    def __init__(self, pdf: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        if pdf is not None:
            self.add(pdf)
            self.description = f"A tool that can be used to semantic search a query the {pdf} PDF's content."
            self.args_schema = FixedPDFSearchToolSchema
            self._generate_description()

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.loader = PyMuPDFLoader(*args, **kwargs)
        self.pages = self.loader.load()
        self.search = FAISS.from_documents(self.pages, OpenAIEmbeddings())

    def _before_run(
        self,
        **kwargs: Any,
    ) -> Any:
        if "pdf" in kwargs:
            self.add(kwargs["pdf"])

    def _run(
		self,
		**kwargs: Any,
    ) -> Any:
        query = kwargs.get('query')
        docs = self.search.similarity_search(query, k=2)
        extract = []
        for doc in docs: 
            extract.append(str(doc.metadata["page"]) + ":", doc.page_content[:300])
        return f"Relevant Content:\n"+"\n".join(extract)
        