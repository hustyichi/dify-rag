# -*- encoding: utf-8 -*-
# File: retrieval_reorganize.py
# Description: None
import logging

from dify_rag.models.constants import CUSTOM_SEP
from dify_rag.models.document import Document
from dify_rag.retrieval.base import RetrievalPostBase

logger = logging.getLogger(__name__)


class TitleStructurePost(RetrievalPostBase):
    def reorganize(
        self,
        query_document: list[Document],
        document_id: str,
        adjunct: dict[str : list[Document]],
    ) -> list[Document]:
        """Reorganize extracted content

        Args:
            query_docs (list[Document]): _description_
            current_docs (list[Document]): _description_

        Returns:
            list[Document]: _description_
        """
        query_docs_title_set = set()
        query_metadata_map = {}
        title_map = {}
        final_documents_list = []
        docs = adjunct.get(document_id)
        if not docs:
            logger.error(f"Document:{document_id} miss adjunct segment")
            return query_document
        for doc in query_document:
            title = content = doc.page_content
            if CUSTOM_SEP in doc.page_content:
                title, content = doc.page_content.split(CUSTOM_SEP)
            query_docs_title_set.add(title)
            key = f"{document_id}_{title}"
            if key not in query_metadata_map:
                query_metadata_map[key] = {"metadata": {}, "content": ""}
            query_metadata_map[key]["metadata"] = doc.metadata
            query_metadata_map[key]["content"] = content

        for doc in docs:
            title = content = doc.page_content
            if CUSTOM_SEP in doc.page_content:
                title, content = doc.page_content.split(CUSTOM_SEP)
            key = f"{document_id}_{title}"
            if title in query_docs_title_set:
                title_map[key] = title_map.get(key, [])
                title_map[key].append(content)

        for key, contents in title_map.items():
            content = query_metadata_map[key]["content"]
            new_content = content
            if len(contents) >= 2:
                # 需要考虑策略自带的字符补充逻辑
                content_index = contents.index(content)
                left, right = content_index, content_index
                start, end = 0, len(contents) - 1
                while len(new_content) < self.max_token and (
                    left - 1 >= start or right + 1 <= end
                ):
                    if right + 1 <= end:
                        right += 1
                        new_content = self.splice_contents(new_content, contents[right])

                    if left - 1 >= start:
                        left -= 1
                        new_content = self.splice_contents(contents[left], new_content)

            doc = Document(
                page_content=new_content, metadata=query_metadata_map[key]["metadata"]
            )
            final_documents_list.append(doc)

        return final_documents_list
