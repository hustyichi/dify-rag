import copy
import re
from typing import Optional

from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.models.document import Document


class MarkdownExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = False,
        remove_images: bool = False,
        encoding: Optional[str] = None,
        autodetect_encoding: bool = True,
        contain_closest_title_levels: int = 0,
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._remove_images = remove_images
        self._encoding = encoding
        self._autodetect_encoding = autodetect_encoding
        self._contain_closest_title_levels = contain_closest_title_levels

    def contain_content(self, content: str):
        """Check whether content is empty"""
        cleaned_string = re.sub(r"\s+", "", content)
        return bool(cleaned_string)

    def trans_titles_and_content(self, content: str, titles: list[str]) -> str:
        titles = titles[-self._contain_closest_title_levels :]
        if self._contain_closest_title_levels == 0:
            titles = []

        if not content:
            return content

        trans_content = ""
        for title in titles:
            if not title:
                continue

            trans_content += f"{title}\n"
        trans_content += content
        return trans_content

    def extract(self) -> list[Document]:
        """Load from file path."""
        tups, tables = self.parse_tups(self._file_path)
        documents = []
        for hierarchy_header, value in tups:
            if not self.contain_content(value):
                continue

            value = value.strip()
            documents.append(
                Document(
                    page_content=self.trans_titles_and_content(value, hierarchy_header),
                    metadata={"titles": hierarchy_header},
                )
            )

        for table in tables:
            if not self.contain_content(table):
                continue

            table = table.strip()
            documents.append(Document(page_content=table))

        return documents

    @staticmethod
    def update_hierarchy_headers(
        hierarchy_headers: list[str], new_header: str
    ) -> list[str]:
        def count_leading_hashes(header: str):
            if not header:
                return 0

            match = re.match(r"^(#+)", header)
            return len(match.group(1)) if match else 0

        def compare_header(header1: str, header2: str):
            header1_count = count_leading_hashes(header1)
            header2_count = count_leading_hashes(header2)

            if header1_count == header2_count:
                return 0
            elif header1_count > header2_count:
                return -1
            else:
                return 1

        def contain_header_content(header: str):
            return header.replace("#", "").replace(" ", "")

        while (
            hierarchy_headers and compare_header(new_header, hierarchy_headers[-1]) >= 0
        ):
            hierarchy_headers.pop()

        if contain_header_content(new_header):
            hierarchy_headers.append(new_header)
        return hierarchy_headers

    def markdown_to_tups(self, markdown_text: str) -> list[tuple[list[str], str]]:
        markdown_tups: list[tuple[list[str], str]] = []
        lines = markdown_text.split("\n")

        hierarchy_headers: list[str] = []
        current_text = ""
        code_block_flag = False

        for line in lines:
            if line.startswith("```"):
                code_block_flag = not code_block_flag
                # enter code block, add split flag
                if code_block_flag:
                    current_text += "\n" + line + "\n"
                # exit code block, add split flag
                else:
                    current_text += line + "\n\n"

                continue

            if code_block_flag:
                current_text += line + "\n"
                continue

            header_match = re.match(r"^#+\s", line)
            if header_match:
                if current_text:
                    markdown_tups.append(
                        (copy.deepcopy(hierarchy_headers), current_text)
                    )

                hierarchy_headers = MarkdownExtractor.update_hierarchy_headers(
                    hierarchy_headers, line
                )
                current_text = ""
            else:
                current_text += line + "\n"
        if current_text:
            markdown_tups.append((copy.deepcopy(hierarchy_headers), current_text))

        return markdown_tups

    def remove_images(self, content: str) -> str:
        """Get a dictionary of a markdown file from its path."""
        pattern = r"!{1}\[\[(.*)\]\]"
        content = re.sub(pattern, "", content)
        return content

    def remove_hyperlinks(self, content: str) -> str:
        """Get a dictionary of a markdown file from its path."""
        pattern = r"\[(.*?)\]\((.*?)\)"
        content = re.sub(pattern, r"\1", content)
        return content

    def extract_tables_and_remainder(self, markdown_text):
        # Standard Markdown table
        table_pattern = re.compile(
            r"""
            (?:\n|^)
            (?:\|.*?\|.*?\|.*?\n)
            (?:\|(?:\s*[:-]+[-| :]*\s*)\|.*?\n)
            (?:\|.*?\|.*?\|.*?\n)+
            """,
            re.VERBOSE,
        )
        tables = table_pattern.findall(markdown_text)
        remainder = table_pattern.sub("", markdown_text)

        # Borderless Markdown table
        no_border_table_pattern = re.compile(
            r"""
            (?:\n|^)
            (?:\S.*?\|.*?\n)
            (?:(?:\s*[:-]+[-| :]*\s*).*?\n)
            (?:\S.*?\|.*?\n)+
            """,
            re.VERBOSE,
        )
        no_border_tables = no_border_table_pattern.findall(remainder)
        tables.extend(no_border_tables)
        remainder = no_border_table_pattern.sub("", remainder)

        return remainder, tables

    def parse_tups(
        self, filepath: str
    ) -> tuple[list[tuple[list[str], str]], list[str]]:
        file_encoding = self._encoding
        if not file_encoding:
            file_encoding = utils.get_encoding(filepath)

        with open(filepath, encoding=file_encoding) as f:
            content = f.read()

            # extract tables from content
            content, tables = self.extract_tables_and_remainder(content)

            if self._remove_hyperlinks:
                content = self.remove_hyperlinks(content)
                tables = [self.remove_hyperlinks(table) for table in tables]

            if self._remove_images:
                content = self.remove_images(content)
                tables = [self.remove_images(table) for table in tables]

            return self.markdown_to_tups(content), tables
