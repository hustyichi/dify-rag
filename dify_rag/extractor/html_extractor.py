from bs4 import BeautifulSoup

from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import html_text, readability
from dify_rag.models.document import Document


class HtmlExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
        contain_closest_title_levels: int = 0,
        title_convert_to_markdown: bool = False,
    ) -> None:
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check
        self._contain_closest_title_levels = contain_closest_title_levels
        self._title_convert_to_markdown = title_convert_to_markdown

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

    @staticmethod
    def convert_to_markdown(html_tag: str, title: str) -> str:
        if not (title and html_tag):
            return title

        html_tag = html_tag.lower()
        if html_tag.startswith("h") and html_tag[1:].isdigit():
            level = int(html_tag[1])
            return f'{"#" * level} {title}'
        else:
            return title

    def trans_titles_and_content(
        self, content: str, titles: list[tuple[str, str]]
    ) -> str:
        titles = titles[-self._contain_closest_title_levels :]
        if self._contain_closest_title_levels == 0:
            titles = []

        if not content:
            return content

        trans_content = ""
        for tag, title in titles:
            if not title:
                continue

            if self._title_convert_to_markdown:
                title = HtmlExtractor.convert_to_markdown(tag, title)

            trans_content += f"{title}\n"
        trans_content += content
        return trans_content

    def trans_meta_titles(self, titles: list[tuple[str, str]]):
        trans_titles = []
        for tag, title in titles:
            if not title:
                continue

            if self._title_convert_to_markdown:
                title = HtmlExtractor.convert_to_markdown(tag, title)

            trans_titles.append(title)
        return trans_titles

    def extract(self) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            text = f.read()

            # preprocess
            text, tables = self.preprocessing(text)

            html_doc = readability.Document(text)
            content, split_contents, titles = html_text.extract_text(
                html_doc.summary(html_partial=True), title=html_doc.title()
            )

            docs = []
            for content, hierarchy_titles in zip(split_contents, titles):
                docs.append(
                    Document(
                        page_content=self.trans_titles_and_content(
                            content, hierarchy_titles
                        ),
                        metadata={"titles": self.trans_meta_titles(hierarchy_titles)},
                    )
                )

            for table in tables:
                docs.append(Document(page_content=table))

            return docs
