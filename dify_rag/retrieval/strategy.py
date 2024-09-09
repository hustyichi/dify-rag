# -*- encoding: utf-8 -*-
# File: strategy.py
# Description: None

from typing import Any, List, Optional

from dify_rag.models.document import Document
from dify_rag.retrieval.base import RetrievalPostBase
from dify_rag.retrieval.schemas import RetrievalPostType


class RetrievalPreStrategy: ...


class RetrievalPostStrategy:

    def __init__(self, strategy_type: RetrievalPostType, max_token: int = 600):
        self.strategy_type = strategy_type
        self._reorganize_strategy = self._get_reorganize_factory(max_token)

    def _get_reorganize_factory(self, max_token: int) -> RetrievalPostBase:
        match self.strategy_type:
            case RetrievalPostType.TITLE_STRUCTURE:
                from dify_rag.retrieval.post.title_structrue import TitleStructurePost

                return TitleStructurePost(max_token)
            case _:
                raise ValueError(
                    f"Retrieval Strategy {self.strategy_type} is not supported."
                )

    def reorganize(
        self, query_document: List[Document], adjucnt: Optional[Any], **kwargs
    ) -> List[Document]:
        return self._reorganize_strategy._reorganize(query_document, adjucnt, **kwargs)
