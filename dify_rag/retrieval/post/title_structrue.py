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
        query_docs_title_map = {}
        query_metadata_map = {}
        title_map = {}
        final_documents_list = []
        for doc in query_document:
            title = content = doc.page_content
            if CUSTOM_SEP in doc.page_content:
                title, content = doc.page_content.split(CUSTOM_SEP)
            query_docs_title_map[document_id] = query_docs_title_map.get(
                document_id, set()
            )
            query_docs_title_map[document_id].add(title)
            key = f"{document_id}_{title}"
            if key not in query_metadata_map:
                query_metadata_map[key] = {"metadata": {}, "content": ""}
            query_metadata_map[key]["metadata"] = doc.metadata
            query_metadata_map[key]["content"] = content

        for document_id, docs in adjunct.items():
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
                while len(new_content) < self.max_token and (
                    left - 1 >= start or right + 1 <= end
                ):
                    if (target == 0 and right + 1 <= end) or (
                        target != 0 and left - 1 >= start
                    ):
                        right += 1
                        new_content = self.splice_contents(new_content, contents[right])
                        target = 1

                    else:
                        left -= 1
                        new_content = self.splice_contents(contents[left], new_content)
                        target = 0

            doc = Document(
                page_content=new_content, metadata=query_metadata_map[key]["metadata"]
            )
            final_documents_list.append(doc)

        logger.info(f"this is normal strategy's result:{final_documents_list}")
        return final_documents_list
