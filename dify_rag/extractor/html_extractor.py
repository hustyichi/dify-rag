import html_text
import readability

from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.models.document import Document


class HtmlExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
    ) -> None:
        self._file_path = file_path

    def extract(self) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            text = f.read()
            html_doc = readability.Document(text)
            title = html_doc.title()
            content = html_text.extract_text(html_doc.summary(html_partial=True))
            txt = f"{title}\n{content}"
            sections = txt.split("\n")

            docs = []
            for sec in sections:
                sec = sec.strip()
                if sec:
                    docs.append(Document(page_content=sec))

            return docs
