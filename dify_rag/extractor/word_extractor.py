import logging
import os
import tempfile
from typing import Optional

import pypandoc

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants
from dify_rag.extractor.html_extractor import HtmlExtractor
from dify_rag.models.document import Document

logger = logging.getLogger(__name__)


class WordExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
        contain_closest_title_levels: int = 0,
        title_convert_to_markdown: bool = False,
        use_first_header_as_title: bool = False,
        seperate_tables: bool = True,
        cut_table_to_line: bool = True,
        split_tags: list[str] = constants.SPLIT_TAGS,
        prevent_duplicate_header: bool = True,
        # dify 本地文件名为 id，可以通过 file_name 传递真实文件名
        file_name: Optional[str] = None,
    ) -> None:
        self._file_path = file_path
        self._file_name = file_name
        self._html_extractor_params = {
            "remove_hyperlinks": remove_hyperlinks,
            "fix_check": fix_check,
            "contain_closest_title_levels": contain_closest_title_levels,
            "title_convert_to_markdown": title_convert_to_markdown,
            "use_first_header_as_title": use_first_header_as_title,
            "seperate_tables": seperate_tables,
            "cut_table_to_line": cut_table_to_line,
            "split_tags": split_tags,
            "prevent_duplicate_header": prevent_duplicate_header,
            "file_name": file_name,
        }

    def extract(self) -> list[Document]:
        original_name = os.path.splitext(
            self._file_name if self._file_name else os.path.basename(self._file_path)
        )[0]
        temp_dir = tempfile.gettempdir()
        temp_html_path = os.path.join(temp_dir, f"{original_name}.html")

        try:
            # 使用 pypandoc 转换文档
            pypandoc.convert_file(
                self._file_path,
                "html",
                outputfile=temp_html_path,
                extra_args=[
                    "--standalone",
                    "--toc",
                    "--toc-depth=6",
                    f"--metadata=title:{original_name}",
                ],
            )
        except Exception as e:
            logger.error(f"Failed to convert document using pandoc: {e}")
            raise

        html_extractor = HtmlExtractor(
            file_path=temp_html_path, **self._html_extractor_params
        )

        documents = html_extractor.extract()

        os.unlink(temp_html_path)

        return documents
