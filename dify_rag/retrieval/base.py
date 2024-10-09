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

    @staticmethod
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

    def reorganize(
        self, query_document: List[Document], *args, **kwargs
    ) -> List[Document]:
        raise NotImplementedError
