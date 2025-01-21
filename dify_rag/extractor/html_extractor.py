import os
from pathlib import Path
from typing import Optional

from dify_rag.extractor import utils
from dify_rag.extractor.emr_extractor import EMRExtractorFactory
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants, html_helper, html_text, readability
from dify_rag.models.document import Document


class HtmlExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: Optional[str] = None,
        file: Optional[str] = None,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
        contain_closest_title_levels: int = 0,
        title_convert_to_markdown: bool = False,
        use_first_header_as_title: bool = False,
        seperate_tables: bool = True,
        cut_table_to_line: bool = True,
        split_tags: list[str] = constants.SPLIT_TAGS,
        prevent_duplicate_header: bool = True,
        use_summary: bool = True,
        # dify 本地文件名为 id，可以通过 file_name 传递真实文件名
        file_name: Optional[str] = None,
    ) -> None:
        self._file_path = file_path
        self._file = file
        if not self._file_path and not self._file:
            raise RuntimeError("file_path or file must exist")
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check
        self._contain_closest_title_levels = contain_closest_title_levels
        self._title_convert_to_markdown = title_convert_to_markdown
        self._use_first_header_as_title = use_first_header_as_title
        self._seperate_tables = seperate_tables
        self._cut_table_to_line = cut_table_to_line
        self._split_tags = split_tags
        self._prevent_duplicate_header = prevent_duplicate_header
        self._use_summary = use_summary
        self._file_name = file_name

    def get_title(self, text_content: str) -> str:
        title = readability.Document(text_content).title()
        if title != constants.NO_TITLE:
            return title

        # get title from file_path
        if self._file_name:
            title = os.path.basename(self._file_name).split(".")[0]
            return title

        return constants.NO_TITLE

    def extract(self) -> list[Document]:
        # check if the file is an EMR file
        if self._file_path:
            extractor = EMRExtractorFactory.get_extractor(self._file_path)
            if extractor:
                return extractor.extract()

            # if not EMR file, then extract as html file
            text_content = Path(self._file_path).read_text(
                encoding=utils.get_encoding(self._file_path)
            )
        else:
            text_content = self._file

        # preprocess
        text, tables, title = html_helper.preprocessing(
            text_content,
            self.get_title(text_content),
            self._use_first_header_as_title,
            self._remove_hyperlinks,
            self._fix_check,
            self._seperate_tables,
            self._prevent_duplicate_header,
        )

        docs = []
        if text:
            if self._use_summary:
                html_doc = readability.Document(text)
                text = html_doc.summary(html_partial=True)
            content, split_contents, titles = html_text.extract_text(
                text,
                title=title,
                split_tags=self._split_tags,
            )
            for content, hierarchy_titles in zip(split_contents, titles):
                docs.append(
                    Document(
                        page_content=html_helper.trans_titles_and_content(
                            content,
                            hierarchy_titles,
                            self._contain_closest_title_levels,
                            self._title_convert_to_markdown,
                        ),
                        metadata={
                            "titles": html_helper.trans_meta_titles(
                                hierarchy_titles, self._title_convert_to_markdown
                            ),
                        },
                    )
                )

        for table in tables:
            if self._cut_table_to_line:
                for doc in html_helper.html_cut_table_handler(table):
                    docs.append(doc)
            else:
                docs.append(
                    html_helper.html_origin_table_handler(
                        table, self._title_convert_to_markdown
                    )
                )
        return docs
