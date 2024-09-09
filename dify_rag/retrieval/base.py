# -*- encoding: utf-8 -*-
# File: base.py
# Description: None

from abc import ABC
from typing import Any, List, Optional

from dify_rag.models.document import Document


class RetrievalPreBase(ABC): ...


class RetrievalPostBase(ABC):
    def __init__(self, max_token: int):
        self.max_token = max_token

    def _reorganize(
        self, query_document: List[Document], *args, **kwargs
    ) -> List[Document]:
        raise NotImplementedError
