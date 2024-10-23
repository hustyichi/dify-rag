import re

from bs4 import BeautifulSoup, Tag

from dify_rag.extractor.emr.constants import BaseEMRConfig
from dify_rag.models.document import Document


def find_element(soup: BeautifulSoup, required_element: dict) -> Tag | None:
    tag = required_element["tag"]
    data_name = required_element["data_name"]
    data_id = required_element["data_id"]
    keyword = required_element["keyword"]
    
    return soup.find(tag, {'data-name': data_name}) or \
        soup.find(tag, {'data-id': data_id}) or \
        soup.find(lambda t: t.name == tag and t.text.startswith(f'{keyword}：'))


def init_metadata(config: BaseEMRConfig) -> dict:
    metadata = {
        "type": config.EMR_TYPE,
    }
    return metadata

def extract_metadata(docs: list[Document]) -> dict:
    """
    Extract the metadata
    """
    metadata = {}
    pattern = r'(\w+)\s*[:：]\s*\[\s*([^\]]+?)\s*\]'
    
    for doc in docs:
        matches = re.findall(pattern, doc.page_content)
        extracted_metadata = {key: value for key, value in matches}
        metadata.update(extracted_metadata)
    
    return metadata

def extract_fields(content: str, config: BaseEMRConfig) -> dict:
    metadata = {}
    for line in content.split("\n\n"):
        for field in config.EXTRACT_FIELDS:
            if line.startswith(field):
                metadata[field] = line.split("：", 1)[1].strip()
                break  # once match the field, break the inner loop
    
    return metadata

def init_basic_metadata(metadata: dict, config: BaseEMRConfig) -> dict:
    basic_metadata = config.BASIC_METADATA
    for key, value in config.BASIC_FIELDS_MAPPING.items():
        basic_metadata[value] = metadata[key]

    return basic_metadata

def extract_basic_info_content(metadata: dict, config: BaseEMRConfig) -> str:
    basic_info_content = f"### {config.BASIC_INFO_TITLE}\n\n"
    for item in config.BASIC_INFO_TOC:
        if item in metadata:
            basic_info_content += f"{item}：{metadata[item]} "
    basic_info_content += "\n\n"
    return basic_info_content

def get_priority_diagnosis(metadata: dict, config: BaseEMRConfig) -> str:
    if metadata.get(config.REVISED_DIAGNOSIS_KEY):
        return metadata[config.REVISED_DIAGNOSIS_KEY]
    if metadata.get(config.INITIAL_DIAGNOSIS_KEY) and \
        metadata.get(config.SUPPLEMENTARY_DIAGNOSIS_KEY):
        return metadata[config.INITIAL_DIAGNOSIS_KEY] + "，" + \
            metadata[config.SUPPLEMENTARY_DIAGNOSIS_KEY]
    if metadata.get(config.INITIAL_DIAGNOSIS_KEY):
        return metadata[config.INITIAL_DIAGNOSIS_KEY]
    return ""

def get_priority_treatment(metadata: dict, config: BaseEMRConfig) -> str:
    if metadata.get(config.TREATMENT_KEY):
        return metadata[config.TREATMENT_KEY]
    if metadata.get(config.PROCEDURE_KEY):
        return metadata[config.PROCEDURE_KEY]
    return ""

def get_basic_metadata(metadata: dict, config: BaseEMRConfig) -> dict:
    basic_metadata = init_basic_metadata(metadata, config)
    basic_metadata[config.EMR_TYPE_KEY] = config.EMR_TYPE
    basic_metadata[config.DIAGNOSIS_KEY] = get_priority_diagnosis(metadata, config)
    basic_metadata[config.TREATMENT_KEY] = get_priority_treatment(metadata, config)
    return basic_metadata
