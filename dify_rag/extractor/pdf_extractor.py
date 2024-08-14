# -*- encoding: utf-8 -*-
# File: pdf_extractor.py
# Description: None

from collections import Counter
from typing import Optional

import pymupdf

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.utils import fix_error_pdf_content, is_gibberish
from dify_rag.models.document import Document


class PdfExtractor(BaseExtractor):
    def __init__(self, file_path: str, file_cache_key: Optional[str] = None) -> None:
        self._file_path = file_path
        self._file_cache_key = file_cache_key

    @staticmethod
    def remove_invalid_char(text_blocks):
        block_content = ""
        for block in text_blocks:
            block_text = block[4]
            if is_gibberish(block_text):
                block_content += block_text
        return fix_error_pdf_content(block_content)

    @staticmethod
    def check_doc_header_or_footer(doc):
        # 页眉和页脚，每页都应该具备且格式相同
        format_map = {"header": [], "footer": []}
        for page in doc:
            text_blocks = page.get_text("blocks")
            if not text_blocks:
                continue
            format_map["header"].append(text_blocks[0][3] - text_blocks[0][1])
            format_map["footer"].append(text_blocks[-1][3] - text_blocks[-1][1])
        headers_count, footer_count = Counter(format_map["header"]), Counter(
            format_map["footer"]
        )
        return (
            max(headers_count.values()) / headers_count.total() >= 0.9,
            max(footer_count.values()) / footer_count.total() >= 0.9,
        )

    @staticmethod
    def split_completion(content, current_split):
        split_content_list = content.split(current_split)
        if len(split_content_list) > 1:
            return split_content_list[0], "".join(split_content_list[1:])
        return "", split_content_list.pop()

    def extract(self) -> list[Document]:
        # 基于pymupdf版本
        doc = pymupdf.open(self._file_path)
        toc = doc.get_toc()
        content, documents = "", []
        header_exist, footer_exist = self.check_doc_header_or_footer(doc)
        for page in doc:
            text_blocks = page.get_text("blocks")
            if header_exist:
                text_blocks = text_blocks[1:]
            if footer_exist:
                text_blocks = text_blocks[:-1]
            content += self.remove_invalid_char(text_blocks)
        if toc:
            prxfix_split = ""
            for _toc in toc:
                current_split = _toc[1]
                prefix, suffix = self.split_completion(content, current_split)
                documents.append(Document(page_content=prxfix_split + prefix))
                prxfix_split, content = current_split, suffix
            documents.append(Document(page_content=prxfix_split + content))
        else:
            documents.append(Document(page_content=content))
        return documents
