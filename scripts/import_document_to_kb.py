# -*- encoding: utf-8 -*-
# File: import_document_to_kb.py
# Description: None

import os

from dify_rag.helper.knowledge_api_base import (
    DifyKnowledgeApi,
    DocumentCustomSplitConfig,
    IndexingTechnique,
    PreProcessingRule,
    PreProcessingRuleEnum,
    ProcessCustomRule,
    ProcessRule,
    ProcessRuleMode,
    RuleSegmentation,
)

DIFY_API_ADDR = ""
DIFY_KB_AUTH = ""
DIFY_DATASET_ID = ""
WORK_FILE_PATH = ""


def traverse_and_upload(folder_path, split_config: DocumentCustomSplitConfig):
    """遍历文件夹并上传所有文件"""
    api_model = DifyKnowledgeApi(base_url=DIFY_API_ADDR, authorization=DIFY_KB_AUTH)

    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            api_model.create_document_by_file(
                dataset_id=DIFY_DATASET_ID,
                file_path=file_path,
                document_custom_split_config=split_config,
            )


def main():
    request_body = DocumentCustomSplitConfig(
        indexing_technique=IndexingTechnique.HIGH_QUALITY,
        process_rule=ProcessRule(
            mode=ProcessRuleMode.CUSTOM,
            rules=ProcessCustomRule(
                pre_processing_rules=[
                    PreProcessingRule(
                        id=PreProcessingRuleEnum.REMOVE_EXTRA_SPACES, enabled=True
                    ),
                    PreProcessingRule(
                        id=PreProcessingRuleEnum.REMOVE_URLS_EMAILS, enabled=True
                    ),
                ],
                segmentation=RuleSegmentation(separator="\n\n\n", max_tokens=100),
            ),
        ),
    )
    traverse_and_upload(WORK_FILE_PATH, request_body)


if __name__ == "__main__":
    main()
