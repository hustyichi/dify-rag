# -*- encoding: utf-8 -*-
# File: normal.py
# Description: None

# -*- encoding: utf-8 -*-
# File: retrieval_reorganize.py
# Description: None
from typing import Dict, List

from dify_rag.models.document import Document
from dify_rag.retrieval.base import RetrievalPostBase


class NormalPost(RetrievalPostBase):
    def new_content_merge(
        self,
        index: int,
        sep: int,
        max_window: int,
        content: str,
        segment_positions: List[int],
        document_position_map: Dict[int, str],
        used_position_list: List[int],
    ):
        position = index
        new_content = content
        while True:
            if index in segment_positions:
                if sep > 0:
                    new_content = self.splice_contents(
                        new_content, document_position_map.get(index)
                    )
                else:
                    new_content = self.splice_contents(
                        document_position_map.get(index), new_content
                    )
                if len(new_content) > self.max_token:
                    break
                used_position_list.append(index)
                index = index + sep
                continue
            else:
                if sep > 0:
                    left, right = index, index + max_window
                else:
                    left, right = index - max_window + 1, index + 1
                _orgin_index = index
                for _index in range(left, right):
                    if _index in segment_positions and _index not in used_position_list:
                        index = _index
                        break
                if _orgin_index == index:
                    break
            # 检查是否超过规定字符长度
            # print(f"index: {index}")
            if sep > 0:
                prev_content = content
                next_content = "".join(
                    document_position_map.get(pos)
                    for pos in range(position + 1, index + 1)
                )
                used_position_list.extend(range(position, index + 1))
            else:
                prev_content = "".join(
                    document_position_map.get(pos) for pos in range(index, position)
                )
                next_content = content
                used_position_list.extend(range(index, position + 1))
            tmp_content = self.splice_contents(prev_content, next_content)
            if len(tmp_content) > self.max_token:
                break
            new_content = tmp_content
        return new_content, used_position_list

    def reorganize(
        self,
        query_document: list[Document],
        adjunct: dict[str, list[Document]],
        max_window: int = 2,
    ) -> list[Document]:
        origin_doc_position_map = {}
        origin_position_content_map = {}
        query_position_list = {}
        reorganized_list = []

        # Process adjunct documents
        try:
            for document_id, docs in adjunct.items():
                origin_doc_position_map[document_id] = {
                    doc.metadata["doc_id"]: doc.metadata["position"] for doc in docs
                }
                origin_position_content_map[document_id] = {
                    doc.metadata["position"]: doc.page_content for doc in docs
                }
        except KeyError:
            return query_document

        # Process query documents
        for doc in query_document:
            document_id = doc.metadata.get("document_id")
            doc.metadata["position"] = origin_doc_position_map.get(document_id, {}).get(
                doc.metadata.get("doc_id")
            )
            query_position_list.setdefault(document_id, []).append(
                doc.metadata["position"]
            )

        # print(f"origin_doc_position_map: {origin_doc_position_map}")
        # print(f"origin_position_content_map: {origin_position_content_map}")
        # print(f"query_position_list: {query_position_list}")
        # Reorganize documents using sliding window
        used_position_map = {}
        for doc in query_document:
            # keep docuements order
            # print(f"this is new doc: {doc}")
            # print(f"used_position_map: {used_position_map}")
            document_id, position = doc.metadata.get("document_id"), doc.metadata.get(
                "position"
            )
            if position in used_position_map.get(document_id, []):
                continue
            segment_positions = query_position_list.get(document_id)
            used_position_list = used_position_map.get(document_id, [])
            # 构建滑动窗口进行相邻切片合并
            new_content = doc.page_content
            new_content, used_position_list = self.new_content_merge(
                position,
                1,
                max_window,
                doc.page_content,
                segment_positions,
                origin_position_content_map.get(document_id, {}),
                used_position_list,
            )
            new_content, used_position_list = self.new_content_merge(
                position,
                -1,
                max_window,
                new_content,
                segment_positions,
                origin_position_content_map.get(document_id, {}),
                used_position_list,
            )
            doc.page_content = new_content
            reorganized_list.append(doc)
            used_position_map.setdefault(document_id, []).extend(used_position_list)
        return reorganized_list
