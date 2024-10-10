import os
import re
from dify_rag.extractor.html_extractor import HtmlExtractor
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import html_text, readability
from dify_rag.models.document import Document





class EMRExtractor(BaseExtractor):
    def __init__(
        self,
        docs: list[Document]
    ) -> None:
        self._docs = docs
        
    def extract(self) -> list[Document]:
        docs = self._docs
        content = ""
        for doc in docs:
            content += "\n" + doc.page_content
        EMR_type = self.EMR_type_recognize(content)
        docs = self.extract_by_type(EMR_type, docs, content)
        return docs

    def EMR_type_recognize(self, content):
        if "[ 谈 话 记 录 ]" in content and "谈话记录" in content:
            return "谈话记录"
        elif "[ 入 院 记 录 ]" in content and "入院记录" in content:
            return "入院记录"
        elif "主诉：" in content and "现病史：" in content and "既往史：" in content:
            return "入院记录"
        elif "[ 手术情同意书 ]" in content:
            return "手术知情同意书"
        elif "简要病情：" in content and "术前诊断：" in content and "拟实施手术名称：" in content:
            return "手术知情同意书"
        return "未知病例"

    def extract_by_type(self, EMR_type, docs, content):
        if EMR_type == "谈话记录":
            return self.extract_talk_record(docs, content)
        elif EMR_type == "入院记录":
            return self.extract_admission_record(docs, content)
        elif EMR_type == "手术知情同意书":
            return self.extract_surgery_informed_consent(docs, content)
        else:
            return docs
        
    def extract_metadata(self, content: str) -> dict:
        """
        Extract the metadata
        """
        pattern = r'(\w+)\s*[:：]\s*\[\s*([^\]]+?)\s*\]'
        # pattern = r'(\w+):\[([^\]]+)\]'
        matches = re.findall(pattern, content)
        metadata = {key: value for key, value in matches}
        return metadata
    
    def extract_talk_record(self, docs, content) -> list[Document]:
        """
        Extract the content and metadata of the talk record
        """
        metadata = {
            "type": "谈话记录",
            "性别": "",
            "年龄": "",
            "科室": "",
            "床号": "",
            "病案号": "",
        }
        
        # Preset key names
        preset_keys = set(metadata.keys())
        
        # Extract the content of all documents
        for doc in docs:
            extracted_metadata = self.extract_metadata(doc.page_content)
            
            # Update all extracted metadata
            metadata.update(extracted_metadata)
        
        content = content.split("| 谈话记录 |  |\n|")[1].split("|")[0]
        content = "## 谈话记录\n\n" + content
        
        # print(metadata)
        # Remove keys not in the preset key list
        # for key in list(metadata.keys()):
        #     if key not in preset_keys:
        #         metadata.pop(key)
        
        doc = Document(page_content=content, metadata=metadata)
        return [doc]
    
    def extract_admission_record(self, docs, content):
        """
        Extract the content and metadata of the admission record
        """
        metadata = {
            "type": "入院记录",
            "性别": "",
            "年龄": "",
            "科室": "",
            "床号": "",
            "病案号": "",
        }
        
        # Preset key names
        # preset_keys = set(metadata.keys())
        
        # Extract the content of all documents
        for doc in docs:
            extracted_metadata = self.extract_metadata(doc.page_content)
            
            # Update all extracted metadata
            metadata.update(extracted_metadata)
        
        # define the fields to extract
        fields = [
            "主诉",
            "现病史",
            "流行病学史",
            "既往史",
            "个人史",
            "婚育史",
            "家族史",
            # "辅助检查",
        ]
        
        # extract the fields
        for line in docs[0].page_content.split("\n\n"):
            for field in fields:
                if line.startswith(field):
                    metadata[field] = line.split("：", 1)[1].strip()
                    break  # once match the field, break the inner loop
        
        final_doc_content = docs[-1].page_content
        if final_doc_content.startswith("| 初步诊断"):
            metadata["初步诊断"] = final_doc_content.split("| 初步诊断： |  |\n| [")[1].split("]")[0]
            match = re.search(r'修正诊断：([\d\.、、\w\W]+?)(?:医师签名|签名时间|\])', final_doc_content)
            if match: 
                # 仅保留诊断内容，去除任何非诊断字符
                metadata["修正诊断"] = re.sub(r'[^\u4e00-\u9fa5\d\.、]+', '', match.group(1).strip())
            else:
                metadata["修正诊断"] = ""
        from pprint import pprint
        pprint(metadata)
        
        content = "## 入院记录\n\n"
        
        toc = [
            "主诉",
            "现病史",
            # "流行病学史",
            # "既往史",
            # "个人史",
            # "婚育史",
            # "家族史",
            "辅助检查",
            "阳性体格检查",
            "阳性辅助检查结果",
            "初步诊断",
            "修正诊断",
            "诊疗方案"
        ]
        for item in toc:
            if item in metadata:
                content += f"### {item}\n\n{metadata[item]}\n\n"
        
        doc = Document(page_content=content, metadata=metadata)
        return [doc]
    
    def extract_surgery_informed_consent(self, docs, content):
        """
        Extract the content and metadata of the surgery informed consent
        """
        metadata = {
            "type": "手术知情同意书",
            "性别": "",
            "年龄": "",
            "科室": "",
            "床号": "",
            "病案号": "",
        }
        
        for doc in docs:
            extracted_metadata = self.extract_metadata(doc.page_content)
            
            # Update all extracted metadata
            metadata.update(extracted_metadata)
        
        # define the fields to extract
        fields = [
            "术中、术后可能出现的各种情况、意外、风险及并发症",
            "针对上述情况，医师根据医疗规范采取在术前、术中、术后预防及治疗措施",
        ]
        
        # extract the fields
        for line in docs[0].page_content.split("\n\n"):
            for field in fields:
                if line.startswith(field):
                    metadata[field] = line.split("：", 1)[1].strip()
                    break  # once match the field, break the inner loop
        
        content = "## 手术知情同意书\n\n"
        
        toc = [
            "简要病情",
            "术前诊断",
            "拟实施手术名称",
            "拟实施麻醉方式",
            "手术指征",
            "手术禁忌症",
            "术前准备",
            "术中、术后可能出现的各种情况、意外、风险及并发症",
            "针对上述情况，医师根据医疗规范采取在术前、术中、术后预防及治疗措施"
        ]
        
        for item in toc:
            if item in metadata:
                content += f"### {item}\n\n{metadata[item]}\n\n"
        
        return [Document(page_content=content, metadata=metadata)]