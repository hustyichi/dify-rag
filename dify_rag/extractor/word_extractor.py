import os
import tempfile
import zipfile
from xml.etree import ElementTree
import logging

import mammoth

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import constants
from dify_rag.extractor.html_extractor import HtmlExtractor
from dify_rag.models.document import Document
from dify_rag.extractor.utils import NS_WORD

logger = logging.getLogger(__name__)


def safe_convert_image(image):
    try:
        with image.open() as image_bytes:
            return {
                "src": f"data:image/{image.content_type};base64,{image_bytes.read().encode('base64')}"
            }
    except Exception:
        pass


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
        split_tags: list[str] = constants.SPLIT_TAGS,
        prevent_duplicate_header: bool = True,
    ) -> None:
        self._file_path = file_path
        self._html_extractor_params = {
            "remove_hyperlinks": remove_hyperlinks,
            "fix_check": fix_check,
            "contain_closest_title_levels": contain_closest_title_levels,
            "title_convert_to_markdown": title_convert_to_markdown,
            "use_first_header_as_title": use_first_header_as_title,
            "seperate_tables": seperate_tables,
            "split_tags": split_tags,
            "prevent_duplicate_header": prevent_duplicate_header,
        }

    def extract(self) -> list[Document]:
        original_name = os.path.splitext(os.path.basename(self._file_path))[0]
        temp_dir = tempfile.gettempdir()
        temp_html_path = os.path.join(temp_dir, f"{original_name}.html")

        try:
            # First try with the original file
            with open(self._file_path, "rb") as docx_file:
                result = mammoth.convert_to_html(
                    docx_file,
                    convert_image=mammoth.images.img_element(safe_convert_image),
                )
                html_content = result.value
        except KeyError as e:
            if "rId" in str(e):
                logger.error(
                    f"Relationship ID error encountered: {e}. Attempting to fix the document..."
                )

                # If fixing didn't work, try a more aggressive approach - extract just the text
                # Extract text directly from the document.xml
                with zipfile.ZipFile(self._file_path, "r") as zip_ref:
                    try:
                        # Try to extract document.xml
                        doc_xml = zip_ref.read("word/document.xml")
                        root = ElementTree.fromstring(doc_xml)

                        # Extract text from paragraphs
                        ns = {"w": NS_WORD}
                        paragraphs = []

                        for para in root.findall(".//w:p", ns):
                            text_runs = []
                            for text_elem in para.findall(".//w:t", ns):
                                if text_elem.text:
                                    text_runs.append(text_elem.text)
                            if text_runs:
                                paragraphs.append(" ".join(text_runs))

                        # Create simple HTML from extracted text
                        html_content = "<html><body>"
                        for para in paragraphs:
                            html_content += f"<p>{para}</p>"
                        html_content += "</body></html>"

                    except Exception as xml_error:
                        logger.error(
                            f"Failed to extract text from document.xml: {xml_error}"
                        )
                        raise
            else:
                # If it's not a relationship ID error, re-raise
                raise

        with open(temp_html_path, "w", encoding="utf-8") as temp_html:
            temp_html.write(html_content)

        html_extractor = HtmlExtractor(
            file_path=temp_html_path, **self._html_extractor_params
        )

        documents = html_extractor.extract()

        os.unlink(temp_html_path)

        return documents
