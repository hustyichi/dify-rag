import os
import re
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import html_text, readability
from dify_rag.models.document import Document

class EMRExtractor(BaseExtractor):
    def __init__(
        self,
        docs: list[Document]
    ) -> None:
        self._docs = docs
        self.TALK_RECORD = "谈话记录"
        self.ADMISSION_RECORD = "入院记录"
        self.SURGERY_CONSENT = "手术知情同意书"
        self.UNKNOWN_CASE = "未知病例"
        self.type_indicators: Dict[str, List[Tuple[str, float]]] = {
            self.TALK_RECORD: [
                ("[ 谈 话 记 录 ]", 0.6),
                ("谈话记录", 0.4),
                ("审核医师", 0.2),
                ("书写医师", 0.2),
            ],
            self.ADMISSION_RECORD: [
                ("[ 入 院 记 录 ]", 0.6),
                ("入院记录", 0.4),
                ("主诉", 0.3),
                ("现病史", 0.3),
                ("既往史", 0.3),
                ("个人史", 0.2),
                ("婚育史", 0.2),
                ("家族史", 0.2),
                ("初步诊断", 0.2),
            ],
            self.SURGERY_CONSENT: [
                ("[ 手术知情同意书 ]", 0.6),
                ("手术知情同意书", 0.4),
                ("简要病情", 0.3),
                ("术前诊断", 0.3),
                ("拟实施手术名称", 0.3),
                ("拟实施麻醉方式", 0.3),
                ("手术风险", 0.2),
                ("主刀医师签名", 0.2),
            ],
        }
    
    def extract(self) -> list[Document]:
        content = "\n".join(doc.page_content for doc in self._docs)
        EMR_type = self.EMR_type_recognize(content)
        return self.extract_by_type(EMR_type, self._docs, content)

    def EMR_type_recognize(self, content: str) -> str:
        scores = {emr_type: 0.0 for emr_type in self.type_indicators}
        
        for emr_type, indicators in self.type_indicators.items():
            for indicator, weight in indicators:
                if indicator in content:
                    scores[emr_type] += weight

        max_score = max(scores.values())
        if max_score > 1.0:
            return max(scores, key=scores.get)
        return self.UNKNOWN_CASE
        
    def extract_metadata(self, content: str) -> dict:
        """
        Extract the metadata
        """
        pattern = r'(\w+)\s*[:：]\s*\[\s*([^\]]+?)\s*\]'
        matches = re.findall(pattern, content)
        metadata = {key: value for key, value in matches}
        return metadata
    
    def extract_by_type(self, EMR_type: str, docs: list[Document], content: str) -> list[Document]:
        if EMR_type == self.TALK_RECORD:
            return self.extract_talk_record(docs, content)
        elif EMR_type == self.ADMISSION_RECORD:
            return self.extract_admission_record(docs, content)
        elif EMR_type == self.SURGERY_CONSENT:
            return self.extract_surgery_informed_consent(docs, content)
        else:
            return docs
    
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
        
        content = content.split("谈话记录 |  |\n|")[1].split("|")[0]
        content = "## 谈话记录\n\n" + content
        
        # Remove keys not in the preset key list
        # for key in list(metadata.keys()):
        #     if key not in preset_keys:
        #         metadata.pop(key)
        
        return [Document(page_content=content, metadata=metadata)]
    
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
        
        return [Document(page_content=content, metadata=metadata)]
    
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

if __name__ == "__main__":
    from dify_rag.extractor.html_extractor import HtmlExtractor
    emr_folder = "test-html/住院病例"
    emr_files = os.listdir(emr_folder)
    print(emr_files)

    emr_file = "手术知情同意书.html"
    html_extractor = HtmlExtractor(os.path.join(emr_folder, emr_file))
    docs = html_extractor.extract()
    emr_extractor = EMRExtractor(docs)
    docs = emr_extractor.extract()
    print(docs[0].page_content)
    print(docs[0].metadata)
