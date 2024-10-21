from dify_rag.extractor.emr.base import BaseHtmlEMRExtractor
from dify_rag.extractor.emr.constants import (BaseEMRConfig,
                                              SurgeryConsentConfig)
from dify_rag.extractor.emr.emr_helper import (extract_fields,
                                               extract_metadata, init_metadata)
from dify_rag.models.document import Document


class SurgeryConsentExtractor(BaseHtmlEMRExtractor):
    @classmethod
    def is_applicable(cls, file_path: str) -> bool:
        return cls.check_applicability(file_path, SurgeryConsentConfig)
    
    def extract_emr(self, docs: list[Document], content: str) -> list[Document]:
        """
        Extract the content and metadata of the surgery informed consent
        """
        
        metadata = init_metadata(SurgeryConsentConfig)
        metadata.update(extract_metadata(docs))
        metadata.update(extract_fields(docs[0].page_content, SurgeryConsentConfig))
        
        content = self._extract_content(metadata, SurgeryConsentConfig)
        
        return [Document(page_content=content, metadata=metadata)]
    
    @staticmethod
    def _extract_content(metadata: dict, config: BaseEMRConfig) -> str:
        content = f"## {config.RECORD_TYPE}\n\n"
        
        for item in config.TOC_ITEMS:
            if item in metadata:
                content += f"### {item}\n\n{metadata[item]}\n\n"
        
        return content