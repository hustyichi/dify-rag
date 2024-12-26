# -*- encoding: utf-8 -*-
# File: pdf_extractor.py
# Description: None

from collections import Counter
from typing import Optional

import pymupdf

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.pdf.toc import generate_toc
from dify_rag.extractor.utils import fix_error_pdf_content, is_gibberish
from dify_rag.models.document import Document


class PdfExtractor(BaseExtractor):
    def __init__(self, file_path: str, file_cache_key: Optional[str] = None) -> None:
        self._file_path = file_path
        self._file_cache_key = file_cache_key

    @staticmethod
    def _get_lines(page_blocks):
        lines = []
        lines_page_idx = []
        for page_idx, text_blocks in enumerate(page_blocks):
            for block in text_blocks:
                block_text = block[4]
                if is_gibberish(block_text):
                    lines.append(block_text.replace("\n", ""))
                    lines_page_idx.append(page_idx)
        return lines, lines_page_idx

    @staticmethod
    def _collect_page_metrics(page):
        """收集单页的页眉页脚度量数据"""
        text_blocks = page.get_text("blocks")
        if not text_blocks:
            return None
        
        header_y, footer_y = float('inf'), float('-inf')
        header_idx, footer_idx = -1, -1
        header_height, footer_height = 0, 0

        for idx, block in enumerate(text_blocks):
            _, y0, _, y1, *_ = block
            if y0 < header_y:
                header_y, header_idx, header_height = y0, idx, y1 - y0
            if y1 > footer_y:
                footer_y, footer_idx, footer_height = y1, idx, y1 - y0

        return {
            'text_blocks': text_blocks,
            'header_idx': header_idx,
            'footer_idx': footer_idx,
            'header_height': header_height,
            'footer_height': footer_height
        }

    @staticmethod
    def _should_remove_headers_footers(page_metrics, threshold=0.9):
        """判断是否应该移除页眉页脚"""
        if not page_metrics:
            return False, False

        header_heights = [m['header_height'] for m in page_metrics if m]
        footer_heights = [m['footer_height'] for m in page_metrics if m]

        def exists_common_height(heights):
            if not heights:
                return False
            _, count = Counter(heights).most_common(1)[0]
            return count / len(heights) >= threshold
            
        return exists_common_height(header_heights), exists_common_height(footer_heights)

    @staticmethod
    def filter_doc_header_or_footer(doc):
        """
        过滤文档中的页眉页脚
        页眉和页脚，每页都应该具备且格式相同
        """
        page_metrics = [PdfExtractor._collect_page_metrics(page) for page in doc]

        header_exists, footer_exists = PdfExtractor._should_remove_headers_footers(page_metrics)

        if not header_exists and not footer_exists:
            return [m['text_blocks'] for m in page_metrics if m]

        filtered_page_blocks = []
        for metrics in page_metrics:
            if not metrics:
                continue

            indices_to_remove = set()
            if header_exists and metrics['header_idx'] != -1:
                indices_to_remove.add(metrics['header_idx'])
            if footer_exists and metrics['footer_idx'] != -1:
                indices_to_remove.add(metrics['footer_idx'])

            filtered_blocks = [
                block for idx, block in enumerate(metrics['text_blocks'])
                if idx not in indices_to_remove
            ]
            filtered_page_blocks.append(filtered_blocks)

        return filtered_page_blocks

    @staticmethod
    def split_completion(content, current_split):
        split_content_list = content.split(current_split)
        if len(split_content_list) > 1:
            return split_content_list[0], "".join(split_content_list[1:])
        return "", split_content_list.pop()

    @staticmethod
    def _get_lines_toc(toc, lines, lines_page_idx):
        """获取TOC的行索引"""
        lines_toc = []
        for level, title, page in toc:
            # 在目标页中查找包含该标题的行
            title_line_idx = next(
                (i for i, idx in enumerate(lines_page_idx)
                    if idx == page - 1 and 
                    (title in lines[i] or title.replace(" ", "") in lines[i])),
                None
                )
            if title_line_idx is not None:
                lines_toc.append((level, title, title_line_idx))
        return lines_toc

    @staticmethod
    def _split_content(lines_toc, lines):
        documents = []

        for i, (current_level, current_title, current_idx) in enumerate(lines_toc):
            titles = []
            stack = []

            for prev_idx in range(i - 1, -1, -1):
                prev_level, prev_title, _ = lines_toc[prev_idx]
                if prev_level < current_level and (not stack or prev_level < stack[-1][0]):
                    stack.append((prev_level, prev_title))

            titles = [title for _, title in sorted(stack)]
            titles.append(current_title)
            
            next_idx = lines_toc[i + 1][2] if i + 1 < len(lines_toc) else len(lines)

            section_content = "".join(lines[current_idx+1:next_idx])

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
        filtered_page_blocks = self.filter_doc_header_or_footer(doc)
        lines, lines_page_idx = self._get_lines(filtered_page_blocks)

        if toc:
            lines_toc = self._get_lines_toc(toc, lines, lines_page_idx)
        else:
            lines_toc = generate_toc(lines)

        if lines_toc:
            documents = self._split_content(lines_toc, lines)
        else:
            content = fix_error_pdf_content("".join(lines))
            documents = [Document(page_content=content)]

        return documents
