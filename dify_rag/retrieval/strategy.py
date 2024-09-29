# -*- encoding: utf-8 -*-
# File: strategy.py
# Description: None

from typing import List

from dify_rag.models.constants import CUSTOM_SEP
from dify_rag.models.document import Document


class RetrievalPreStrategy: ...


class RetrievalPostStrategy:

    def __init__(self, max_token: int = 600):
        self.max_token = max_token

    def reorganize(
        self, query_document: List[Document], *args, **kwargs
    ) -> List[Document]:
        if not query_document:
            return []
        example = query_document[0]
        if CUSTOM_SEP in example.page_content:
            from dify_rag.retrieval.post.title_structrue import TitleStructurePost

            return TitleStructurePost(self.max_token).reorganize(
                query_document, *args, **kwargs
            )
        else:
            from dify_rag.retrieval.post.normal import NormalPost

            return NormalPost(self.max_token).reorganize(
                query_document, *args, **kwargs
            )
