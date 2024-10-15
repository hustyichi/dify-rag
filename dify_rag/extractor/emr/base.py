import re
from bs4 import BeautifulSoup

from abc import abstractmethod
from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import html_helper, html_text, readability
from dify_rag.models.document import Document
from .emr_helper import find_element
from .constants import BaseEMRConfig
class BaseEMRExtractor(BaseExtractor):
    """Interface for extract EMR files."""
        
    @classmethod
    @abstractmethod
    def is_applicable(cls, file_path: str) -> bool:
        raise NotImplementedError
    
class BaseHtmlEMRExtractor(BaseEMRExtractor):
    def __init__(self, file_path: str):
        self._file_path = file_path
        self._docs: list[Document] = []
        self._content: str = ""

    @classmethod
    def check_applicability(cls, file_path: str, config: BaseEMRConfig) -> bool:
        if not file_path.endswith(".html"):
            return False
        
        with open(file_path, 'r', encoding=utils.get_encoding(file_path)) as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        header = soup.find('header')
    
        if not header:
            return False
        
        title_text = header.text.strip().replace(" ", "")
        
        if config.is_applicable(title_text):
            if all(find_element(soup, required_element) for required_element in config.REQUIRED_ELEMENTS):
                return True
        return False
        
    def extract(self) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            text = f.read()
            
            # preprocess
            text, tables, title = html_helper.preprocessing(
                        content=text,
                        title=readability.Document(text).title(),
                        use_first_header_as_title=False,
                        remove_hyperlinks=True,
                        fix_check=True,
                        seperate_tables=True,
                        )
            
            html_doc = readability.Document(text)
            content, split_contents, titles = html_text.extract_text(
                html_doc.summary(html_partial=True), title=html_doc.title()
            )

            docs = []
            for content, hierarchy_titles in zip(split_contents, titles):
                docs.append(
                    Document(
                        page_content=html_helper.trans_titles_and_content(
                            content=content,
                            titles=hierarchy_titles,
                            contain_closest_title_levels=0,
                            title_convert_to_markdown=False,
                        ),
                        metadata={
                            "titles": html_helper.trans_meta_titles(
                                titles=hierarchy_titles,
                                title_convert_to_markdown=False
                            )
                        },
                    )
                )

            for table in tables:
                docs.append(
                    Document(
                        page_content=table["table"],
                        metadata={
                            "titles": html_helper.trans_meta_titles(
                                titles=table["titles"],
                                title_convert_to_markdown=False
                            )
                        },
                    )
                )
        
        content = "\n".join([doc.page_content for doc in docs])
        return self.extract_emr(docs, content)
    
    @abstractmethod
    def extract_emr(self, docs: list[Document], content: str) -> list[Document]:
        raise NotImplementedError