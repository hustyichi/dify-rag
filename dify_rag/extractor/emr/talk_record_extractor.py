import re

from dify_rag.extractor.emr.base import BaseHtmlEMRExtractor
from dify_rag.extractor.emr.constants import BaseEMRConfig, TalkRecordConfig
from dify_rag.extractor.emr.emr_helper import (extract_metadata,
                                               extract_basic_info_content,
                                               get_basic_metadata,
                                               init_metadata)
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
        basic_metadata = get_basic_metadata(metadata, TalkRecordConfig)
        
        return [Document(page_content=content, metadata=basic_metadata)]
    
    @staticmethod
    def _extract_talk_record(content: str, config: BaseEMRConfig) -> dict:
        pattern = config.TALK_RECORD_PATTERN
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return {config.EMR_TYPE: match.group(1).strip()}
        else:
            return {}
    
    @staticmethod
    def _extract_content(metadata: dict, config: BaseEMRConfig) -> str:
        content = f"## {config.EMR_TYPE}\n\n"
        
        content += extract_basic_info_content(metadata)
        
        for item in config.TOC_ITEMS:
            if item in metadata:
                content += f"{metadata[item]}\n\n"
        
        return content
        

