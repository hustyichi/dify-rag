# -*- encoding: utf-8 -*-
# File: test_retrieval_unit_test.py
# Description: None

import unittest

from dify_rag.models.constants import CUSTOM_SEP
from dify_rag.models.document import Document
from dify_rag.retrieval.post.normal import NormalPost
from dify_rag.retrieval.post.title_structrue import TitleStructurePost
from tests.log import logger


class TestRetrieval(unittest.TestCase):
    def test_normal(self):
        adjunct = {
            "test": [
                Document(
                    page_content=str(i),
                    metadata={"doc_id": i, "position": i, "document_id": "test"},
                )
                for i in range(100)
            ]
        }
        query_list = [
            Document(
                page_content="1",
                metadata={"doc_id": 1, "position": 1, "document_id": "test"},
            ),
            Document(
                page_content="3",
                metadata={"doc_id": 3, "position": 3, "document_id": "test"},
            ),
            Document(
                page_content="6",
                metadata={"doc_id": 6, "position": 6, "document_id": "test"},
            ),
            Document(
                page_content="10",
                metadata={"doc_id": 10, "position": 10, "document_id": "test"},
            ),
        ]
        self.assertEqual(
            NormalPost(2000).reorganize(query_list, "test", adjunct),
            [
                Document(
                    page_content="123",
                    metadata={"doc_id": 1, "position": 1, "document_id": "test"},
                ),
                Document(
                    page_content="6",
                    metadata={"doc_id": 6, "position": 6, "document_id": "test"},
                ),
                Document(
                    page_content="10",
                    metadata={"doc_id": 10, "position": 10, "document_id": "test"},
                ),
            ],
        )

    def test_title_structrue(self):
        adjunct = {
            "test": [
                Document(
                    page_content=f"test1_1{CUSTOM_SEP}test1_11",
                    metadata={"document_id": "test"},
                ),
                Document(
                    page_content=f"test1_1{CUSTOM_SEP}test1_12",
                    metadata={"document_id": "test"},
                ),
                Document(
                    page_content=f"test1_2{CUSTOM_SEP}test1_21",
                    metadata={"document_id": "test"},
                ),
            ],
            "test2": [
                Document(
                    page_content=f"test2_1{CUSTOM_SEP}test2_11",
                    metadata={"document_id": "test2"},
                ),
                Document(
                    page_content=f"test2_2{CUSTOM_SEP}test2_11",
                    metadata={"document_id": "test2"},
                ),
                Document(
                    page_content=f"test2_3{CUSTOM_SEP}test3_11",
                    metadata={"document_id": "test2"},
                ),
            ],
        }
        query_list = [
            Document(
                page_content=f"test1_1{CUSTOM_SEP}test1_12",
                metadata={"document_id": "test"},
            )
        ]
        self.assertEqual(
            TitleStructurePost(2000).reorganize(query_list, "test", adjunct),
            [
                Document(
                    page_content="test1_11test1_12", metadata={"document_id": "test"}
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
