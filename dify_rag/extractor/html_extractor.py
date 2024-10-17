from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants, html_helper, html_text, readability
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
        split_tags: list[str] = constants.SPLIT_TAGS,
    ) -> None:
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check
        self._contain_closest_title_levels = contain_closest_title_levels
        self._title_convert_to_markdown = title_convert_to_markdown
        self._use_first_header_as_title = use_first_header_as_title
        self._seperate_tables = seperate_tables
        self._split_tags = split_tags

    def extract(self) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            text = f.read()

            # preprocess
            text, tables, title = html_helper.preprocessing(
                text,
                readability.Document(text).title(),
                self._use_first_header_as_title,
                self._remove_hyperlinks,
                self._fix_check,
                self._seperate_tables,
            )

            html_doc = readability.Document(text)
            content, split_contents, titles = html_text.extract_text(
                html_doc.summary(html_partial=True),
                title=title,
                split_tags=self._split_tags,
            )

            docs = []
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
                            )
                        },
                    )
                )

            for table in tables:
                docs.append(
                    Document(
                        page_content=table["table"],
                        metadata={
                            "titles": html_helper.trans_meta_titles(
                                table["titles"], self._title_convert_to_markdown
                            )
                        },
                    )
                )

            return docs
