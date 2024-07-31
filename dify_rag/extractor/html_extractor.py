from bs4 import BeautifulSoup

from dify_rag.extractor import constants, utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.models.document import Document


class HtmlExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        chunk_size: int = constants.DEFAULT_CHUNK_SIZE,
    ) -> None:
        self._file_path = file_path
        self._chunk_size = chunk_size

    def _pre_process(self, soup: BeautifulSoup) -> BeautifulSoup:
        # clean unchecked checkboxes and radio buttons
        match_inputs = soup.find_all("input", {"type": ["checkbox", "radio"]})
        for input_tag in match_inputs:
            if not input_tag.has_attr("checked"):
                next_span = input_tag.find_next_sibling("span")
                if next_span:
                    next_span.extract()
                input_tag.extract()

        return soup

    def _trans_to_docs(self, soup: BeautifulSoup) -> list[Document]:
        docs = []
        current_content = ""

        for tag in soup.children:
            data = tag.get_text("").strip()
            if not data:
                continue

            merge_content = current_content + ("\n" if current_content else "") + data
            if len(merge_content) > self._chunk_size:
                docs.append(Document(page_content=current_content))
                current_content = data
            else:
                current_content = merge_content

        if current_content:
            docs.append(Document(page_content=current_content))
        return docs

    def extract(self) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            soup = BeautifulSoup(f, "html.parser")
            soup = self._pre_process(soup)

            return self._trans_to_docs(soup)
