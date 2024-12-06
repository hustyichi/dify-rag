import os
import re
import tempfile

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants
from dify_rag.extractor.html_extractor import HtmlExtractor
from dify_rag.extractor.unstructured.constants import EPUB_HTML_TEMPLATE

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
        self._html_extractor_params = {
            'remove_hyperlinks': remove_hyperlinks,
            'fix_check': fix_check,
            'contain_closest_title_levels': contain_closest_title_levels,
            'title_convert_to_markdown': title_convert_to_markdown,
            'use_first_header_as_title': use_first_header_as_title,
            'seperate_tables': seperate_tables,
            'split_tags': split_tags,
            'prevent_duplicate_header': prevent_duplicate_header,
        }

    def _get_book_title(self, book):
        title = book.get_metadata('DC', 'title')
        if title:
            book_title = title[0][0]
            return re.sub(r'^#+', '', book_title)
        return os.path.splitext(os.path.basename(self._file_path))[0]

    @staticmethod
    def _process_soup_element(soup):
        for element in soup.find_all():
            if element.get('xmlns'):
                del element['xmlns']
            if element.get('xml:lang'):
                del element['xml:lang']

    @staticmethod
    def _add_title_to_soup(soup, book_title):
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = book_title
            return
            
        head_tag = soup.find('head')
        if not head_tag:
            head_tag = soup.new_tag('head')
            if soup.html:
                soup.html.insert(0, head_tag)
            else:
                soup.append(head_tag)
        head_tag.append(soup.new_tag('title', string=book_title))

    def extract(self):
        book = epub.read_epub(self._file_path)
        book_title = self._get_book_title(book)
        
        texts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.content, 'html.parser')
                self._process_soup_element(soup)
                self._add_title_to_soup(soup, book_title)

                body = soup.find('body')
                text = str(body.decode_contents()) if body else str(soup)
                texts.append(text)

        html_content = EPUB_HTML_TEMPLATE.format(
            book_title=book_title,
            content="".join(texts)
            )

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
