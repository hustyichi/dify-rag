import re

from dify_rag.extractor.emr.base import BaseHtmlEMRExtractor
from dify_rag.extractor.emr.constants import (AdmissionRecordConfig,
                                              BaseEMRConfig)
from dify_rag.extractor.emr.emr_helper import (extract_fields,
                                               extract_metadata,
                                               extract_basic_info_content,
                                               get_basic_metadata,
                                               init_metadata)
from dify_rag.models.document import Document


class AdmissionRecordExtractor(BaseHtmlEMRExtractor):
    
    @classmethod
    def is_applicable(cls, file_path: str) -> bool:
        return cls.check_applicability(file_path, AdmissionRecordConfig)
    
    def extract_emr(self, docs: list[Document], content: str) -> list[Document]:
        """
        Extract the content and metadata of the admission record
        """
        metadata = init_metadata(AdmissionRecordConfig)
        metadata.update(extract_metadata(docs))
        metadata.update(extract_fields(docs[0].page_content, AdmissionRecordConfig))
        metadata.update(self._extract_diagnosis(docs, AdmissionRecordConfig))
        
        content = self._extract_content(metadata, AdmissionRecordConfig)
        
        basic_metadata = get_basic_metadata(metadata, AdmissionRecordConfig)
        
        return [Document(page_content=content, metadata=basic_metadata)]
    
    @staticmethod
    def _extract_diagnosis(docs: list[Document], config: BaseEMRConfig) -> dict:
        metadata = {}
        
        for doc in docs:
            content = doc.page_content
            if content.startswith(config.DIAGNOSIS_START):
                initial_diagnosis_match = re.search(config.INITIAL_DIAGNOSIS_PATTERN, content, re.DOTALL)
                if initial_diagnosis_match:
                    metadata[config.INITIAL_DIAGNOSIS_KEY] = initial_diagnosis_match.group(1).strip()
                
                revised_diagnosis_match = re.search(config.REVISED_DIAGNOSIS_PATTERN, content, re.DOTALL)
                if revised_diagnosis_match:
                    metadata[config.REVISED_DIAGNOSIS_KEY] = re.sub(config.DIAGNOSIS_CLEAN_PATTERN, '', revised_diagnosis_match.group(1).strip())
                
                
                supplementary_diagnosis_match = re.search(config.SUPPLEMENTARY_DIAGNOSIS_PATTERN, content, re.DOTALL)
                if supplementary_diagnosis_match:
                    metadata[config.SUPPLEMENTARY_DIAGNOSIS_KEY] = re.sub(config.DIAGNOSIS_CLEAN_PATTERN, '', supplementary_diagnosis_match.group(1).strip())
                
                if metadata:
                    break
        
        return metadata
    
    @staticmethod
    def _extract_content(metadata: dict, config: BaseEMRConfig) -> str:
        content = f"## {config.EMR_TYPE}\n\n"
        
        content += extract_basic_info_content(metadata)
        
        for item in config.TOC_ITEMS:
            if item in metadata:
                content += f"### {item}\n\n{metadata[item]}\n\n"
        
        return content
    