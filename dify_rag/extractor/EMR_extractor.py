from dify_rag.extractor.extractor_base import BaseExtractor

from dify_rag.extractor.emr import (
    TalkRecordExtractor,
    AdmissionRecordExtractor,
    SurgeryConsentExtractor
)

class EMRExtractorFactory:
    @staticmethod
    def get_extractor(file_path: str) -> BaseExtractor:
        if TalkRecordExtractor.is_applicable(file_path):
            return TalkRecordExtractor(file_path)
        elif AdmissionRecordExtractor.is_applicable(file_path):
            return AdmissionRecordExtractor(file_path)
        elif SurgeryConsentExtractor.is_applicable(file_path):
            return SurgeryConsentExtractor(file_path)
        else:
            raise ValueError(f"Unrecognized EMR types: {file_path}")