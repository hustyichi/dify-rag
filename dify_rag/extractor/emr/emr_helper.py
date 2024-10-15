import re
from bs4 import BeautifulSoup
from .constants import BaseEMRConfig
from dify_rag.models.document import Document

def find_element(soup, required_element):
    tag = required_element["tag"]
    data_name = required_element["data_name"]
    data_id = required_element["data_id"]
    keyword = required_element["keyword"]
    
    return soup.find(tag, {'data-name': data_name}) or \
        soup.find(tag, {'data-id': data_id}) or \
        soup.find(lambda t: t.name == tag and t.text.startswith(f'{keyword}：'))


def init_metadata(config: BaseEMRConfig) -> dict:
    metadata = {
        "type": config.RECORD_TYPE,
        **{field: "" for field in config.BASIC_FIELDS}
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
