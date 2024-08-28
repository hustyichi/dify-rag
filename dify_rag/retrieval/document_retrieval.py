# -*- encoding: utf-8 -*-
# File: document_retrieval.py
# Description: None

from dify_rag.models.constants import CUSTOM_SEP
from dify_rag.models.document import Document


def retrieval2reorganize(
    query_docs: list[Document],
    current_docs_segemts: dict[str : list[Document]],
    max_token: int = 500,
) -> list[Document]:
    """Reorganize extracted content

    Args:
        query_docs (list[Document]): _description_
        current_docs (list[Document]): _description_

    Returns:
        list[Document]: _description_
    """
    query_docs_title_map = {}
    query_metadata_map = {}
    title_map = {}
    final_documents_list = []
    for doc in query_docs:
        document_id = doc.metadata.get("document_id")
        title = content = doc.page_content
        if CUSTOM_SEP in doc.page_content:
            title, content = doc.page_content.split(CUSTOM_SEP)
        query_docs_title_map[document_id] = query_docs_title_map.get(document_id, set())
        query_docs_title_map[document_id].add(title)
        key = f"{document_id}_{title}"
        if key not in query_metadata_map:
            query_metadata_map[key] = {"metadata": {}, "content": ""}
        query_metadata_map[key]["metadata"] = doc.metadata
        query_metadata_map[key]["content"] = content

    for document_id, docs in current_docs_segemts.items():
        titles = query_docs_title_map.get(document_id)
        for doc in docs:
            title = content = doc.page_content
            if CUSTOM_SEP in doc.page_content:
                title, content = doc.page_content.split(CUSTOM_SEP)
            key = f"{document_id}_{title}"
            if title in titles:
                title_map[key] = title_map.get(key, [])
                title_map[key].append(content)

    for key, contents in title_map.items():
        content = query_metadata_map[key]["content"]
        new_content = content
        if len(contents) >= 2:
            # 需要考虑策略自带的字符补充逻辑
            content_index = contents.index(content)
            left, right, target = content_index, content_index, 0
            start, end = 0, len(contents) - 1
            while len(new_content) < max_token and (
                left - 1 >= start or right + 1 <= end
            ):
                if (target == 0 and right + 1 <= end) or (
                    target != 0 and left - 1 >= start
                ):
                    right += 1
                    new_content = splice_contents(new_content, contents[right])
                    target = 1

                else:
                    left -= 1
                    new_content = splice_contents(contents[left], new_content)
                    target = 0

        doc = Document(
            page_content=new_content, metadata=query_metadata_map[key]["metadata"]
        )
        final_documents_list.append(doc)

    return final_documents_list


def splice_contents(prev: str, next: str):
    start_char = next[0]
    prev_right = len(prev) - 1
    while 0 <= prev_right:
        if prev[prev_right] == start_char:
            similar_segment = prev[prev_right:]
            if similar_segment == next[: len(similar_segment)]:
                next = next[len(similar_segment) :]
                break
        prev_right -= 1
    return prev + next
