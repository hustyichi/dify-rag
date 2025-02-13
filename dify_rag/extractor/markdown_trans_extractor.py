import os
import tempfile
from typing import Optional

import markdown2

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants
from dify_rag.extractor.html_extractor import HtmlExtractor
from dify_rag.models import constants as global_constants
from dify_rag.models.document import Document


class MarkdownExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
        contain_closest_title_levels: int = 0,
        title_convert_to_markdown: bool = False,
        use_first_header_as_title: bool = False,
        seperate_tables: bool = True,
        split_tags: list[str] = constants.SPLIT_TAGS,
        prevent_duplicate_header: bool = True,
        use_summary: bool = False,
        choices_return_full_text_marker: str = global_constants.CHOICES_RETURN_FULL_TEXT_MARKER,
    ) -> None:
        self._file_path = file_path
        self._html_extractor_params = {
            'remove_hyperlinks': remove_hyperlinks,
            'fix_check': fix_check,
            'contain_closest_title_levels': contain_closest_title_levels,
            'title_convert_to_markdown': title_convert_to_markdown,
            'use_first_header_as_title': use_first_header_as_title,
            'seperate_tables': seperate_tables,
            'split_tags': split_tags,
            'prevent_duplicate_header': prevent_duplicate_header,
            'use_summary': use_summary,
        }
        self._choices_return_full_text_marker = choices_return_full_text_marker

    def _handle_full_text_marker(self, md_content: str) -> Optional[list[Document]]:
        if not self._choices_return_full_text_marker:
            return None

        first_line, *rest = md_content.strip().split('\n', 1)
        return [Document(page_content=rest[0])] if rest and first_line == self._choices_return_full_text_marker else None

    def extract(self) -> list[Document]:
        with open(self._file_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()

        # 如果 md_content 以全文标记开头，则返回全文
        if docs := self._handle_full_text_marker(md_content):
            return docs

        markdowner = markdown2.Markdown(extras=['tables', 'fenced-code-blocks', 'toc'])
        html_content = markdowner.convert(md_content)

        original_name = os.path.splitext(os.path.basename(self._file_path))[0]
        temp_dir = tempfile.gettempdir()
        temp_html_path = os.path.join(temp_dir, f"{original_name}.html")
        with open(temp_html_path, 'w', encoding='utf-8') as temp_html:
            temp_html.write(html_content)

        html_extractor = HtmlExtractor(
            file_path=temp_html_path,
            **self._html_extractor_params
        )

        documents = html_extractor.extract()

        os.unlink(temp_html_path)

        return documents
