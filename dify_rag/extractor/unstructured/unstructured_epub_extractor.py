import os
import warnings

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import (constants, html_helper, html_text,
                                     readability)
from dify_rag.models import constants as global_constants
from dify_rag.models.document import Document

warnings.filterwarnings('ignore', category=FutureWarning)

class UnstructuredEpubExtractor(BaseExtractor):
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
    ) -> None:
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check
        self._contain_closest_title_levels = contain_closest_title_levels
        self._title_convert_to_markdown = title_convert_to_markdown
        self._use_first_header_as_title = use_first_header_as_title
        self._seperate_tables = seperate_tables
        self._split_tags = split_tags
        self._prevent_duplicate_header = prevent_duplicate_header

    def extract(self):
        book = epub.read_epub(self._file_path, options={"ignore_ncx": True})
        
        title = book.get_metadata('DC', 'title')
        if title:
            book_title = title[0][0]
        else:
            book_title = os.path.splitext(os.path.basename(self._file_path))[0]

        docs = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title_tag.string = book_title
                else:
                    head_tag = soup.find('head')
                    if head_tag:
                        head_tag.append(soup.new_tag('title', string=book_title))
                    else:
                        head_tag = soup.new_tag('head')
                        head_tag.append(soup.new_tag('title', string=book_title))
                        if soup.html:
                            soup.html.insert(0, head_tag)
                        else:
                            soup.append(head_tag)
                text = str(soup)
                
                text, tables, title = html_helper.preprocessing(
                    text,
                    readability.Document(text).title(),
                    self._use_first_header_as_title,
                    self._remove_hyperlinks,
                    self._fix_check,
                    self._seperate_tables,
                    self._prevent_duplicate_header,
                )

                html_doc = readability.Document(text)
                content, split_contents, titles = html_text.extract_text(
                    html_doc.summary(html_partial=True),
                    title=title,
                    split_tags=self._split_tags,
                )

                item_docs = []
                for content, hierarchy_titles in zip(split_contents, titles):
                    item_docs.append(
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
                    item_docs.append(
                        Document(
                            page_content=table["table"],
                            metadata={
                                "titles": html_helper.trans_meta_titles(
                                    table["titles"], self._title_convert_to_markdown
                                ),
                                "content_type": global_constants.ContentType.TABLE,
                            },
                        )
                    )
                
                docs.extend(item_docs)

        return docs
