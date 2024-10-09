# -*- encoding: utf-8 -*-
# File: normal.py
# Description: None

import logging

# -*- encoding: utf-8 -*-
# File: retrieval_reorganize.py
# Description: None
from typing import Dict, List

from dify_rag.models.document import Document
from dify_rag.retrieval.base import RetrievalPostBase

logger = logging.getLogger(__name__)


class NormalPost(RetrievalPostBase):
    def content_merge(
        self,
        index: int,
        max_window: int,
        content: str,
        segment_positions: List[int],
        document_position_map: Dict[int, str],
        used_position_list: List[int],
    ):
        # 判断左右索引
        left, right = index, index
        right_nums = 0
        left_nums = 0
        new_content = content
        target_left, target_right = left, right
        while True:
            if (
                right in segment_positions
                and right not in used_position_list
                and right_nums <= max_window
            ):
                next = "".join(
                    document_position_map.get(i) for i in range(target_right, right + 1)
                )
                _content = self.splice_contents(new_content, next)
                if len(_content) > self.max_token:
                    break
                new_content = _content
                used_position_list.append(right)
                target_right = right
                right_nums = 0
            if (
                left in segment_positions
                and left not in used_position_list
                and left_nums <= max_window
            ):
                prev = "".join(
                    document_position_map.get(i) for i in range(left, target_left)
                )
                _content = self.splice_contents(prev, new_content)
                if len(_content) > self.max_token:
                    break
                new_content = _content
                used_position_list.append(left)
                target_left = left
                left_nums = 0
            if right_nums <= max_window:
                right += 1
                right_nums += 1
            if left_nums <= max_window:
                left -= 1
                left_nums += 1
            if right_nums > max_window and left_nums > max_window:
                break
        return new_content, used_position_list

    def reorganize(
        self,
        query_document: list[Document],
        document_id: str,
        adjunct: dict[str, list[Document]],
        max_window: int = 2,
    ) -> list[Document]:
        origin_doc_position_map = {}
        origin_position_content_map = {}
        segment_positions = []
        reorganized_list = []

        # Process adjunct documents
        try:
            docs = adjunct[document_id]
            origin_doc_position_map = {
                doc.metadata["doc_id"]: doc.metadata["position"] for doc in docs
            }
            origin_position_content_map = {
                doc.metadata["position"]: doc.page_content for doc in docs
            }
        except KeyError:
            return query_document

        # Process query documents
        for doc in query_document:
            doc.metadata["position"] = origin_doc_position_map.get(
                doc.metadata.get("doc_id")
            )
            segment_positions.append(doc.metadata["position"])

        logger.info(
            f"document_id:{document_id}, segment_positions: {segment_positions}"
        )
        # Reorganize documents using sliding window
        used_position_list = []
        for doc in query_document:
            # keep docuements order
            # logger.info(f"used_position_map: {used_position_map}")
            position = doc.metadata.get("position")
            if position in used_position_list:
                continue
            # 构建滑动窗口进行相邻切片合并
            new_content = doc.page_content
            new_content, _used_position_list = self.content_merge(
                position,
                max_window,
                new_content,
                segment_positions,
                origin_position_content_map,
                used_position_list,
            )
            doc.page_content = new_content
            reorganized_list.append(doc)
            used_position_list.extend(_used_position_list)
        return reorganized_list
