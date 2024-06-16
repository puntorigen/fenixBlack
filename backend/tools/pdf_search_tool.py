from typing import Any, Optional, Type

from embedchain.models.data_type import DataType
from pydantic.v1 import BaseModel, Field

from crewai_tools import BaseTool
#from ..rag.rag_tool import RagTool

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

search = None

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
    pdf: Optional[str] = None
    query: Optional[str] = None

    def __init__(self, pdf: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        if pdf is not None:
            self.add(pdf)
            self.name = "Search a PDF's content"
            self.description = f"A tool that can be used to semantic search a query the {pdf} PDF's content."
            self.args_schema = FixedPDFSearchToolSchema
            self._generate_description() 

    def add(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        global search
        loader = PyMuPDFLoader(*args) #, **kwargs
        pages = loader.load()
        search = FAISS.from_documents(pages, OpenAIEmbeddings())

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
        global search
        query = kwargs.get('query')
        docs = search.similarity_search(query, k=2)
        extract = []
        for doc in docs: 
            extract.append(str(doc.metadata["page"]) + ":", doc.page_content[:300])
        return f"Relevant Content:\n"+"\n".join(extract)
        