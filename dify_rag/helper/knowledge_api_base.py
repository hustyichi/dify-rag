# -*- encoding: utf-8 -*-
"""
Dify Knowledge API client implementation.
"""

import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DifyKnowledgeApiError(Exception):
    """Base exception for Dify Knowledge API errors"""
    pass


class IndexingTechnique(str, Enum):
    HIGH_QUALITY = "high_quality"
    ECONOMY = "economy"


class ProcessRuleMode(str, Enum):
    AUTOMATIC = "automatic" 
    CUSTOM = "custom"


class PreProcessingRuleEnum(str, Enum):
    REMOVE_EXTRA_SPACES = "remove_extra_spaces"
    REMOVE_URLS_EMAILS = "remove_urls_emails"


class DatasetPermissionEnum(str, Enum):
    ONLY_ME = "only_me"
    ALL_TEAM_MEMBERS = "all_team_members" 
    PARTIAL_MEMBERS = "partial_members"


class DatasetProviderEnum(str, Enum):
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
    rules: Optional[ProcessCustomRule] = None


class DocumentCustomSplitConfig(BaseModel):
    name: Optional[str] = None
    indexing_technique: IndexingTechnique = IndexingTechnique.HIGH_QUALITY
    process_rule: ProcessRule = ProcessRule()


class Segment(BaseModel):
    content: str
    answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    enabled: bool = True


class DifyKnowledgeApi:
    """Client for interacting with Dify Knowledge API"""

    API_VERSION = "v1"

    def __init__(self, base_url: str, authorization: str):
        """Initialize the API client.

        Args:
            base_url: Base URL for the API
            authorization: Authorization token
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.authorization = authorization

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        return {
            "Authorization": f"Bearer {self.authorization}",
            "Content-Type": "application/json",
        }

    def _build_url(self, *path_segments: str) -> str:
        """Build full API URL from path segments."""
        return urljoin(self.base_url, "/".join([self.API_VERSION, *path_segments]))

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API.

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
        logger.debug(f"Making request with kwargs: {kwargs}")

        try:
            response = requests.request(method, endpoint, **kwargs)
            if response.status_code != 200:
                logger.error(f"Request failed with status {response.status_code}: {response.text}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise DifyKnowledgeApiError(f"API request failed: {str(e)}")

    def create_document_by_text(
        self,
        dataset_id: str,
        document_name: str,
        content: str,
        document_custom_split_config: Optional[DocumentCustomSplitConfig] = None,
    ) -> Dict[str, Any]:
        """Create document from text content.

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
        """Create document from file.

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
    ) -> Dict[str, Any]:
        """Update document by uploading a file.

        Args:
            dataset_id: ID of the dataset
            document_id: ID of the document to update
            file_path: Path to file
            document_custom_split_config: Custom split configuration

        Returns:
            API response
        """
        url = self._build_url("datasets", dataset_id, f"documents/{document_id}/update_by_file")
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

    def update_document_by_text(
        self,
        dataset_id: str,
        document_id: str,
        document_name: str,
        content: str,
        document_custom_split_config: Optional[DocumentCustomSplitConfig] = None,
    ) -> Dict[str, Any]:
        """Update document content.

        Args:
            dataset_id: ID of the dataset
            document_id: ID of the document to update
            document_name: Name of the document
            content: Text content
            document_custom_split_config: Custom split configuration

        Returns:
            API response
        """
        url = self._build_url("datasets", dataset_id, f"documents/{document_id}/update_by_text")

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
        indexing_technique: IndexingTechnique = IndexingTechnique.HIGH_QUALITY,
        permission: DatasetPermissionEnum = DatasetPermissionEnum.ONLY_ME,
        provider: DatasetProviderEnum = DatasetProviderEnum.VENDOR,
        external_knowledge_api: Optional[str] = None,
        external_knowledge_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new dataset.

        Args:
            name: Dataset name
            description: Dataset description
            indexing_technique: Indexing technique to use
            permission: Dataset permission level
            provider: Dataset provider
            external_knowledge_api: External knowledge API URL
            external_knowledge_id: External knowledge ID

        Returns:
            API response
        """
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

    def list_dataset(self, page: int, limit: int) -> Dict[str, Any]:
        """List datasets with pagination.

        Args:
            page: Page number
            limit: Items per page

        Returns:
            API response
        """
        if not page or not limit:
            raise ValueError("Page and limit parameters are required")

        url = self._build_url("datasets")
        params = {"page": str(page), "limit": str(limit)}

        return self._make_request("GET", url, params=params)

    def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """Delete a dataset.

        Args:
            dataset_id: ID of dataset to delete

        Returns:
            API response
        """
        if not dataset_id:
            raise ValueError("Dataset ID is required")

        url = self._build_url("datasets")
        params = {"dataset_id": dataset_id}

        return self._make_request("GET", url, params=params)

    def get_document_batch_status(self, dataset_id: str, batch: str) -> Dict[str, Any]:
        """Get document batch embedding status.

        Args:
            dataset_id: Dataset ID
            batch: Batch ID

        Returns:
            API response
        """
        if not dataset_id or not batch:
            raise ValueError("Dataset ID and batch ID are required")

        url = self._build_url("datasets", f"{dataset_id}/documents/{batch}/indexing-status")
        return self._make_request("GET", url)

    def delete_document(self, dataset_id: str, document_id: str) -> Dict[str, Any]:
        """Delete a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID to delete

        Returns:
            API response
        """
        if not dataset_id or not document_id:
            raise ValueError("Dataset ID and document ID are required")

        url = self._build_url("datasets", f"{dataset_id}/documents/{document_id}")
        return self._make_request("DELETE", url)

    def get_document_list(
        self,
        dataset_id: str,
        key_word: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get list of documents in dataset.

        Args:
            dataset_id: Dataset ID
            key_word: Search keyword
            page: Page number
            limit: Items per page

        Returns:
            API response
        """
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
    ) -> Dict[str, Any]:
        """Add segments to a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segments: List of segments to add

        Returns:
            API response
        """
        if not dataset_id or not document_id or not segments:
            raise ValueError("Dataset ID, document ID and segments are required")

        url = self._build_url("datasets", f"{dataset_id}/documents/{document_id}/segments")
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
    ) -> Dict[str, Any]:
        """Update a segment in a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Segment ID to update
            segment: Updated segment data

        Returns:
            API response
        """
        if not dataset_id or not document_id or not segment:
            raise ValueError("Dataset ID, document ID and segment are required")

        url = self._build_url("datasets", f"{dataset_id}/documents/{document_id}/segments/{segment_id}")
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
    ) -> Dict[str, Any]:
        """Get segments in a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            keyword: Search keyword
            status: Filter by status

        Returns:
            API response
        """
        url = self._build_url("datasets", f"{dataset_id}/documents/{document_id}/segments")
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
    ) -> Dict[str, Any]:
        """Delete a segment from a document.

        Args:
            dataset_id: Dataset ID
            document_id: Document ID
            segment_id: Segment ID to delete

        Returns:
            API response
        """
        url = self._build_url("datasets", f"{dataset_id}/documents/{document_id}/segments/{segment_id}")
        return self._make_request("DELETE", url)
