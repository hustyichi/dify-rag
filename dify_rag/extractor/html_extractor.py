import html_text
import readability
from bs4 import BeautifulSoup

from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.models.document import Document

NO_TITLE = "[no-title]"


class HtmlExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
    ) -> None:
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check

    @staticmethod
    def convert_table_to_markdown(table) -> str:
        md = []
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            row_text = (
                "| " + " | ".join(cell.get_text(strip=True) for cell in cells) + " |"
            )
            md.append(row_text)

            if row.find("th"):
                header_sep = "| " + " | ".join("---" for _ in cells) + " |"
                md.append(header_sep)

        return "\n".join(md)

    def preprocessing(self, content: str) -> tuple:
        soup = BeautifulSoup(content, "html.parser")

        # clean hyperlinks
        if self._remove_hyperlinks:
            a_tags = soup.find_all("a")
            for tag in a_tags:
                text = tag.get_text()
                cleaned_text = text.replace("\n", " ").replace("\r", "")
                tag.replace_with(cleaned_text)

        # clean unchecked checkboxes and radio buttons
        if self._fix_check:
            match_inputs = soup.find_all("input", {"type": ["checkbox", "radio"]})
            for input_tag in match_inputs:
                if not input_tag.has_attr("checked"):
                    next_span = input_tag.find_next_sibling("span")
                    if next_span:
                        next_span.extract()
                    input_tag.extract()

        # split tables
        tables_md = []
        tables = soup.find_all("table")
        for table in tables:
            table_md = HtmlExtractor.convert_table_to_markdown(table)
            tables_md.append(table_md)
            table.decompose()

        return str(soup), tables_md

    def extract(self) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            text = f.read()

            # preprocess
            text, tables = self.preprocessing(text)

            html_doc = readability.Document(text)
            content = html_text.extract_text(html_doc.summary(html_partial=True))

            title = html_doc.title()
            if title != NO_TITLE:
                txt = f"{title}\n{content}"
            else:
                txt = content

            sections = txt.split("\n")
            clean_sections = []
            for sec in sections:
                sec = sec.strip()
                if sec:
                    clean_sections.append(sec)

            docs = [Document(page_content="\n\n".join(clean_sections))]

            for table in tables:
                docs.append(Document(page_content=table))

            return docs
