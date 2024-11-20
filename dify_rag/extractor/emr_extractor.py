from typing import Optional

from dify_rag.extractor.emr import (AdmissionRecordExtractor,
                                    SurgeryConsentExtractor,
                                    TalkRecordExtractor)
from dify_rag.extractor.extractor_base import BaseExtractor


class EMRExtractorFactory:
    EXTRACTORS = [
        TalkRecordExtractor,
        AdmissionRecordExtractor,
        SurgeryConsentExtractor
    ]

    @staticmethod
    def get_extractor(file_path: str) -> Optional[BaseExtractor]:
        for extractor_class in EMRExtractorFactory.EXTRACTORS:
            if extractor_class.is_applicable(file_path):
                return extractor_class(file_path)
        return None
