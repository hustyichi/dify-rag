# -*- encoding: utf-8 -*-
# File: strategy.py
# Description: None

import logging
from typing import List

from dify_rag.models.constants import CUSTOM_SEP
from dify_rag.models.document import Document

logger = logging.getLogger(__name__)


class RetrievalPreStrategy: ...


class RetrievalPostStrategy:

    def __init__(self, max_token: int = 2000):
        self.max_token = max_token

    @staticmethod
    def format_segments(documents: List[Document]):
        return [
            {
                "content": document.page_content,
                "doc_id": document.metadata.get("doc_id"),
                "document_id": document.metadata.get("document_id"),
                "score": document.metadata.get("score"),
            }
            for document in documents
        ]

    def _reorganize(self, query_document: List[Document], document_id, *args, **kwargs):
        example = query_document[0]
        if CUSTOM_SEP in example.page_content:
            from dify_rag.retrieval.post.title_structrue import TitleStructurePost

            return TitleStructurePost(self.max_token).reorganize(
                query_document, document_id, *args, **kwargs
            )
        else:
            from dify_rag.retrieval.post.normal import NormalPost

            return NormalPost(self.max_token).reorganize(
                query_document, document_id, *args, **kwargs
            )

    def reorganize(
        self, query_documents: List[Document], *args, **kwargs
    ) -> List[Document]:
        logger.info(f"original_documents: {self.format_segments(query_documents)}")
        if not query_documents:
            return []
        document_map = {}
        for document in query_documents:
            document_id = document.metadata.get("document_id")
            if document_id not in document_map:
                document_map[document_id] = [document]
            else:
                document_map[document_id].append(document)

        final_documents = []

        for document_id, documents in document_map.items():
            reorganized_documents = self._reorganize(
                documents, document_id, *args, **kwargs
            )
            logger.info(
                f"running document:{document_id}, these're segments:{self.format_segments(documents)}, handle segment: {self.format_segments(reorganized_documents)}"
            )
            final_documents.extend(reorganized_documents)
        logger.info(f"this is final_documents:{self.format_segments(final_documents)}")
        return final_documents
