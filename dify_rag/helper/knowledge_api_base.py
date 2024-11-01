# -*- encoding: utf-8 -*-
# File: import_file_to_knowledgebase.py
# Description: None

import json
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DifyKnowledgeApiError(Exception):
    """Base exception for DifyKnowledgeApi"""

    pass


class IndexingTechnique(Enum):
    HIGH_QUALITY = "high_quality"
    ECONOMY = "economy"


class ProcessRuleMode(Enum):
    AUTOMATIC = "automatic"
    CUSTOM = "custom"


class PreProcessingRuleEnum(Enum):
    REMOVE_EXTRA_SPACES = "remove_extra_spaces"
    REMOVE_URLS_EMAILS = "remove_urls_emails"


class DatasetPermissionEnum(Enum):
    ONLY_ME = "only_me"
    ALL_TEAM_MEMBERS = "all_team_members"
    PARTIAL_MEMBERS = "partial_members"


class DatasetProviderEnum(Enum):
    VENDOR = "vendor"
    EXTERNAL = "external"


class PreProcessingRule(BaseModel):
    id: PreProcessingRuleEnum
    enabled: bool


class RuleSegmentation(BaseModel):
    separator: str = "\n\n\n"
    max_tokens: int = 10000


class ProcessCustomRule(BaseModel):
    pre_processing_rules: List[PreProcessingRule] = [
        PreProcessingRule(id=PreProcessingRuleEnum.REMOVE_EXTRA_SPACES, enabled=True),
        PreProcessingRule(id=PreProcessingRuleEnum.REMOVE_URLS_EMAILS, enabled=True),
    ]
    segmentation: RuleSegmentation = RuleSegmentation()


class ProcessRule(BaseModel):
    mode: ProcessRuleMode = ProcessRuleMode.AUTOMATIC
    rules: Optional[ProcessCustomRule]


class DocumentCustomSplitConfig(BaseModel):
    name: Optional[str] = None
    indexing_technique: IndexingTechnique = IndexingTechnique.HIGH_QUALITY
    process_rule: ProcessRule


class Segment(BaseModel):
    content: str
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    enabled: Optional[bool] = True


class DifyKnowledgeApi:
    """Client for interacting with Dify Knowledge API"""

    API_VERSION = "v1"

    def __init__(self, base_url: str, authorization: str):
        """Initialize the API client

        Args:
            base_url: Base URL for the API
            authorization: Authorization token
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.authorization = authorization

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for requests"""
        return {
            "Authorization": f"Bearer {self.authorization}",
            "Content-Type": "application/json",
        }

    def _build_url(self, *path_segments: str) -> str:
        """Build full API URL from path segments"""
        return urljoin(self.base_url, "/".join([self.API_VERSION, *path_segments]))

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            JSON response

        Raises:
            DifyKnowledgeApiError: If request fails
        """

        if not kwargs.get("headers"):
            kwargs["headers"] = {**self._get_headers()}
        logger.error(kwargs)

        try:
            response = requests.request(method, endpoint, **kwargs)
            if response.status_code != 200:
                logger.error(f"show something error in request:{response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise DifyKnowledgeApiError(f"API request failed: {str(e.__dict__)}")

    def create_document_by_text(
        self,
        dataset_id: str,
        document_name: str,
        content: str,
        document_custom_split_config: Optional[DocumentCustomSplitConfig] = None,
    ) -> Dict[str, Any]:
        """Create document from text content

        Args:
            dataset_id: ID of the dataset
            document_name: Name of the document
            content: Text content
            document_custom_split_config: Custom split configuration

        Returns:
            API response
        """
        url = self._build_url("datasets", dataset_id, "document/create_by_text")

        config = document_custom_split_config or DocumentCustomSplitConfig()
        request_body = {
            **json.loads(config.model_dump_json()),
            "name": document_name,
            "text": content,
        }

        return self._make_request("POST", url, data=json.dumps(request_body))

    def create_document_by_file(
        self,
        dataset_id: str,
        file_path: str,
        document_custom_split_config: Optional[DocumentCustomSplitConfig] = None,
    ) -> Dict[str, Any]:
        """Create document from file

        Args:
            dataset_id: ID of the dataset
            file_path: Path to file
            document_custom_split_config: Custom split configuration

        Returns:
            API response
        """
        url = self._build_url("datasets", dataset_id, "document/create_by_file")

        config = document_custom_split_config or DocumentCustomSplitConfig()

        with open(file_path, "rb") as f:
            files = {"file": f}
            return self._make_request(
                "POST",
                url,
                files=files,
                data={"data": config.model_dump_json()},
                headers={"Authorization": self._get_headers()["Authorization"]},
            )

    def update_document_by_file(
        self,
        dataset_id: str,
        document_id: str,
        file_path: str,
        document_custom_split_config: Optional[DocumentCustomSplitConfig] = None,
    ):
        """Update document by uploading a file"""
        url = self._build_url(
            "datasets", dataset_id, f"documents/{document_id}/update_by_file"
        )

        config = document_custom_split_config or DocumentCustomSplitConfig()
        # Prepare form data
        with open(file_path, "rb") as f:
            files = {
                "file": f,
            }
            return self._make_request(
                "POST",
                url,
                files=files,
                data={"data": config.model_dump_json()},
                headers={"Authorization": self._get_headers()["Authorization"]},
            )

    def update_document_by_text(
        self,
        dataset_id: str,
        document_id: str,
        document_name: str,
        content: str,
        document_custom_split_config: Optional[DocumentCustomSplitConfig],
    ):
        """create document by content"""
        url = self._build_url(
            "datasets", dataset_id, f"documents/{document_id}/update_by_text"
        )

        config = document_custom_split_config or DocumentCustomSplitConfig()
        request_body = {
            **json.loads(config.model_dump_json()),
            "name": document_name,
            "text": content,
        }

        return self._make_request("POST", url, data=json.dumps(request_body))

    def create_dataset(
        self,
        name: str,
        description: Optional[str] = None,
        indexing_technique: Optional[
            IndexingTechnique
        ] = IndexingTechnique.HIGH_QUALITY,
        permission: DatasetPermissionEnum = DatasetPermissionEnum.ONLY_ME,
        provider: Optional[DatasetProviderEnum] = DatasetProviderEnum.VENDOR,
        external_knowledge_api: Optional[str] = None,
        external_knowledge_id: Optional[str] = None,
    ):
        """create dataset"""
        url = self._build_url("datasets")

        request_body = {
            "name": name,
            "indexing_technique": indexing_technique.value,
            "description": description,
            "permission": permission.value,
            "provider": provider.value,
        }
        if external_knowledge_api:
            request_body["external_knowledge_api"] = external_knowledge_api
        if external_knowledge_id:
            request_body["external_knowledge_id"] = external_knowledge_id

        return self._make_request("POST", url, data=json.dumps(request_body))

    def list_dataset(self, page: int, limit: int):
        """list dataset"""
        if not page or not limit:
            raise BaseException("Missing params: page or limit")

        url = self._build_url("datasets")

        params = {"page": str(page), "limit": str(limit)}

        return self._make_request("GET", url, params=params)

    def delete_dataset(self, dataset_id: str):
        """delete dataset"""
        if not dataset_id:
            raise BaseException("Missing params: dataset_id")

        url = self._build_url("datasets")

        params = {"dataset_id": dataset_id}

        return self._make_request("GET", url, params=params)

    def get_document_batch_status(self, dataset_id: str, batch: str):
        """get document batch embedding status"""
        if not dataset_id or not batch:
            raise BaseException("Missing params: dataaset_id or batch")

        url = self._build_url(
            "datasets", f"{dataset_id}/documents/{batch}/indexing-status"
        )

        return self._make_request("GET", url)

    def delete_document(self, dataset_id: str, document_id: str):
        """delete document"""
        if not dataset_id or not document_id:
            raise BaseException("Missing params: dataset_id or document_id")

        url = self._build_url("datasets", f"{dataset_id}/documents/{document_id}")

        return self._make_request("DELETE", url)

    def get_document_list(
        self,
        dataset_id: str,
        key_word: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        """get documents in dataset"""
        params = {}
        if page:
            params["page"] = str(page)
        if limit:
            params["limit"] = str(limit)
        if key_word:
            params["keyword"] = key_word
        url = self._build_url("datasets", f"{dataset_id}/documents")

        return self._make_request("GET", url, params=params)

    def add_segment_to_document(
        self, dataset_id: str, document_id: str, segments: List[Segment]
    ):
        if not dataset_id or not document_id or not segments:
            raise BaseException("Missing Params: dataset_id, document_id, segment")

        url = self._build_url(
            "datasets", f"{dataset_id}/documents/{document_id}/segments"
        )

        return self._make_request(
            "POST",
            url,
            json={"segments": [seg.model_dump() for seg in segments]},
        )

    def update_segment_to_document(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
        segment: Segment,
    ):
        if not dataset_id or not document_id or not segment:
            raise BaseException("Missing Params: dataset_id, document_id, segment")

        url = self._build_url(
            "datasets", f"{dataset_id}/documents/{document_id}/segments/{segment_id}"
        )

        return self._make_request(
            "POST",
            url,
            json={"segment": segment.model_dump()},
        )

    def get_segment_in_document(
        self,
        dataset_id: str,
        document_id: str,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """获取文档固定片段信息"""
        url = self._build_url(
            "datasets", f"{dataset_id}/documents/{document_id}/segments"
        )
        config = {}
        if keyword:
            config["keyword"] = keyword
        if status:
            config["status"] = status

        return self._make_request("GET", url, json=config)

    def delete_segment_in_document(
        self,
        dataset_id: str,
        document_id: str,
        segment_id: str,
    ):
        """获取文档固定片段信息"""
        url = self._build_url(
            "datasets", f"{dataset_id}/documents/{document_id}/segments/{segment_id}"
        )

        return self._make_request("DELETE", url)


if __name__ == "__main__":
    dify_api = DifyKnowledgeApi(
        "http://127.0.0.1:5001", "dataset-ZyGmvgMME0KdHlIzoJX5kjgB"
    )
    # dify_api.create_dataset("dify测试", description="ceshi")
    # dify_api.create_document_by_file(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "入院记录/62e72f0b401c4a5dd1c301ec.html",
    #     document_custom_split_config=request_body,
    # )
    # dify_api.create_document_by_text(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "文本上传.txt",
    #     "这是测试文本",
    #     document_custom_split_config=request_body,
    # )
    # dify_api.update_document_by_file(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "c53c6b14-6479-44e4-9b69-c41ba3f64558",
    #     "入院记录/62e72f0b401c4a5dd1c301ec.html",
    #     document_custom_split_config=request_body,
    # )
    # dify_api.update_document_by_text(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "c53c6b14-6479-44e4-9b69-c41ba3f64558",
    #     "文本上传.txt",
    #     "这是测试文本",
    #     document_custom_split_config=request_body,
    # )
    # dify_api.get_document_batch_status("7e07707e-b4fb-4de0-9c48-ae3714eb624c", "0")
    # dify_api.delete_document(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "c53c6b14-6479-44e4-9b69-c41ba3f64558",
    # )
    # print(dify_api.get_document_list("7e07707e-b4fb-4de0-9c48-ae3714eb624c"))
    # dify_api.add_segment_to_document(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "827ae1ff-5df2-4548-b572-e0b8236e9579",
    #     segments=[Segment(content="测试segment", keywords=["测试"])],
    # )
    # print(
    #     dify_api.get_segment_in_document(
    #         "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #         "827ae1ff-5df2-4548-b572-e0b8236e9579",
    #     )
    # )
    # dify_api.delete_segment_in_document(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "827ae1ff-5df2-4548-b572-e0b8236e9579",
    #     "79ae66a4-2680-47de-9abf-27c08061ee3c",
    # )
    # dify_api.update_segment_to_document(
    #     "7e07707e-b4fb-4de0-9c48-ae3714eb624c",
    #     "827ae1ff-5df2-4548-b572-e0b8236e9579",
    #     "d17cf458-e43e-4327-b11f-a091e2153415",
    #     segment=Segment(content="还是测试文本111", keywords=["测试"]),
    # )
