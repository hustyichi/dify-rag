import copy
import re

from bs4 import BeautifulSoup

from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants, html_text, readability
from dify_rag.models.document import Document


class HtmlExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
        contain_closest_title_levels: int = 0,
        title_convert_to_markdown: bool = False,
        use_first_header_as_title: bool = False,
        seperate_tables: bool = True,
    ) -> None:
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check
        self._contain_closest_title_levels = contain_closest_title_levels
        self._title_convert_to_markdown = title_convert_to_markdown
        self._use_first_header_as_title = use_first_header_as_title
        self._seperate_tables = seperate_tables

    @staticmethod
    def convert_table_to_markdown(table) -> str:
        md = []
        rows = table.find_all("tr")
        first_row = True

        for row in rows:
            cells = row.find_all(["th", "td"])
            row_text = (
                "| " + " | ".join(cell.get_text(strip=True) for cell in cells) + " |"
            )
            md.append(row_text)

            if row.find("th") or first_row:
                header_sep = "| " + " | ".join("---" for _ in cells) + " |"
                md.append(header_sep)
                first_row = False

        return "\n".join(md)

    def recursive_preprocess_tables(self, soup: BeautifulSoup, title: str) -> list:
        table_with_titles = []
        title_stack = []
        if title:
            title_stack.append((constants.TITLE_KEY, title))

        match_tags = [
            key for key in constants.TAG_HIERARCHY.keys() if key != constants.TITLE_KEY
        ] + ["table"]
        for tag in soup.find_all(match_tags):

            if tag.name in constants.TAG_HIERARCHY:
                level = constants.TAG_HIERARCHY[tag.name]
                title_text = tag.get_text(strip=True)

                while (
                    title_stack and constants.TAG_HIERARCHY[title_stack[-1][0]] <= level
                ):
                    title_stack.pop()

                title_stack.append((tag.name, title_text))

            elif tag.name == "table":
                table_md = HtmlExtractor.convert_table_to_markdown(tag)
                tag.decompose()

                table_with_titles.append(
                    {"table": table_md, "titles": copy.deepcopy(title_stack)}
                )

        return table_with_titles

    def preprocessing(self, content: str, title: str) -> tuple:
        soup = BeautifulSoup(content, "html.parser")

        header = soup.find(["h1", "h2"])
        if header and self._use_first_header_as_title:
            title = header.get_text().strip()

        # clean header contents
        for tag in soup.find_all(re.compile("^h[1-6]$")):
            tag_text = tag.get_text()
            tag.clear()
            tag.string = tag_text.replace("\n", " ").replace("\r", "")

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

        tables = []
        if self._seperate_tables:
            tables = self.recursive_preprocess_tables(soup, title)
        return str(soup), tables, title

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
            text, tables, title = self.preprocessing(
                text, readability.Document(text).title()
            )

            html_doc = readability.Document(text)
            content, split_contents, titles = html_text.extract_text(
                html_doc.summary(html_partial=True), title=title
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
                docs.append(
                    Document(
                        page_content=table["table"],
                        metadata={"titles": self.trans_meta_titles(table["titles"])},
                    )
                )

            return docs
