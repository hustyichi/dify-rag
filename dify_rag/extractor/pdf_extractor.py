# -*- encoding: utf-8 -*-
# File: pdf_extractor.py
# Description: None

from typing import Optional

import pymupdf

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.pdf import constants, pdf_helper
from dify_rag.extractor.pdf.toc import generate_toc
from dify_rag.extractor.utils import fix_error_pdf_content
from dify_rag.models.document import Document


class PdfExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        file_cache_key: Optional[str] = None,
        split_tags: list[str] = constants.SPLIT_TAGS,
    ) -> None:
        self._file_path = file_path
        self._file_cache_key = file_cache_key
        self._split_tags = split_tags

    @staticmethod
    def _split_content(lines_toc, lines):
        documents = []

        if lines_toc[0][2] > 1:
            documents.append(
                Document(
                    page_content=fix_error_pdf_content(
                        "".join(lines[0:lines_toc[0][2]])
                    )
                )
            )

        for i, (current_level, current_title, current_idx) in enumerate(lines_toc):
            titles = []
            stack = []

            for prev_idx in range(i - 1, -1, -1):
                prev_level, prev_title, _ = lines_toc[prev_idx]
                if prev_level < current_level and (not stack or prev_level < stack[-1][0]):
                    stack.append((prev_level, prev_title))

            titles = [fix_error_pdf_content(title) for _, title in sorted(stack)]
            titles.append(fix_error_pdf_content(current_title))

            next_idx = lines_toc[i + 1][2] if i + 1 < len(lines_toc) else len(lines)

            section_content = fix_error_pdf_content("".join(lines[current_idx+1:next_idx]))

            documents.append(Document(
                page_content=section_content,
                metadata={"titles": titles}
            ))
        return documents

    def extract(self) -> list[Document]:
        # 基于pymupdf版本
        doc = pymupdf.open(self._file_path)
        toc = doc.get_toc()
        content, documents = "", []
        filtered_page_blocks = pdf_helper.filter_doc_header_or_footer(doc)
        lines, lines_page_idx = pdf_helper.get_lines(filtered_page_blocks)

        if toc:
            lines_toc = pdf_helper.get_lines_toc(toc, lines, lines_page_idx)
        else:
            lines_toc = generate_toc(lines)

        if self._split_tags and lines_toc:
            lines_toc = [t for t in lines_toc if t[0] in self._split_tags]

        if lines_toc:
            documents = self._split_content(lines_toc, lines)
        else:
            content = fix_error_pdf_content("".join(lines))
            documents = [Document(page_content=content, metadata={"titles":[]})]

        doc.close()
        return documents
