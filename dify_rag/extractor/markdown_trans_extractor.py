import os
import tempfile

import markdown2

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants
from dify_rag.extractor.html_extractor import HtmlExtractor
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

    def extract(self) -> list[Document]:
        original_name = os.path.splitext(os.path.basename(self._file_path))[0]
        temp_dir = tempfile.gettempdir()
        temp_html_path = os.path.join(temp_dir, f"{original_name}.html")

        with open(self._file_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()

        markdowner = markdown2.Markdown(extras=['tables', 'fenced-code-blocks', 'toc'])
        html_content = markdowner.convert(md_content)

        with open(temp_html_path, 'w', encoding='utf-8') as temp_html:
            temp_html.write(html_content)

        html_extractor = HtmlExtractor(
            file_path=temp_html_path,
            **self._html_extractor_params
        )

        documents = html_extractor.extract()

        os.unlink(temp_html_path)

        return documents
