from typing import List
from bs4 import BeautifulSoup
import re

from .base import BaseHtmlEMRExtractor
from .emr_helper import find_element, extract_metadata
from .constants import TalkRecordConfig, BaseEMRConfig
from .emr_helper import init_metadata, extract_metadata, extract_fields
from dify_rag.models.document import Document

class TalkRecordExtractor(BaseHtmlEMRExtractor):
    @classmethod
    def is_applicable(cls, file_path: str) -> bool:
        return cls.check_applicability(file_path, TalkRecordConfig)
    
    def extract_emr(self, docs: list[Document], content: str) -> list[Document]:
        """
        Extract the content and metadata of the talk record
        """
        metadata = init_metadata(TalkRecordConfig)
        metadata.update(extract_metadata(docs))
        metadata.update(self._extract_talk_record(content, TalkRecordConfig))
        
        content = self._extract_content(metadata, TalkRecordConfig)
        
        return [Document(page_content=content, metadata=metadata)]
    
    @staticmethod
    def _extract_talk_record(content: str, config: BaseEMRConfig) -> dict:
        pattern = config.TALK_RECORD_PATTERN
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return {config.RECORD_TYPE: match.group(1).strip()}
        else:
            return {}
    
    @staticmethod
    def _extract_content(meta: dict, config: BaseEMRConfig) -> str:
        content = f"## {config.RECORD_TYPE}\n\n"
        
        content += f"{meta[config.RECORD_TYPE]}\n\n"
        
        return content
        

