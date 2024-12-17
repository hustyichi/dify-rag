import os
import re
import tempfile
import zipfile

from bs4 import BeautifulSoup

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants
from dify_rag.extractor.html_extractor import HtmlExtractor

EPUB_HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{book_title}</title>
</head>
<body>{content}</body>
</html>''' 

class EpubExtractor(BaseExtractor):
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

    def _get_book_title(self, epub_zip):
        try:
            for name in epub_zip.namelist():
                if name.endswith('.opf'):
                    with epub_zip.open(name) as f:
                        soup = BeautifulSoup(f.read(), 'xml')
                        title = soup.find('dc:title')
                        if title:
                            return re.sub(r'^#+', '', title.text)
        except:
            pass
        return os.path.splitext(os.path.basename(self._file_path))[0]

    @staticmethod
    def _process_soup_element(soup):
        for element in soup.find_all():
            if element.get('xmlns'):
                del element['xmlns']
            if element.get('xml:lang'):
                del element['xml:lang']

    def extract(self):
        with zipfile.ZipFile(self._file_path) as epub_zip:
            book_title = self._get_book_title(epub_zip)

            texts = []
            html_files = [f for f in epub_zip.namelist() if f.endswith(('.html', '.xhtml'))]

            for html_file in html_files:
                with epub_zip.open(html_file) as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    self._process_soup_element(soup)

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
