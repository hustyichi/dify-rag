import re
from bs4 import BeautifulSoup

from dify_rag.extractor import utils
from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.html import html_text, readability
from dify_rag.models.document import Document

class EMRExtractor(BaseExtractor):
    def __init__(
        self,
        file_path: str,
        remove_hyperlinks: bool = True,
        fix_check: bool = True,
        contain_closest_title_levels: int = 0,
        title_convert_to_markdown: bool = False,
        TALK_RECORD: str = "谈话记录",
        ADMISSION_RECORD: str = "入院记录",
        SURGERY_CONSENT: str = "手术知情同意书",
    ) -> None:
        self._file_path = file_path
        self._remove_hyperlinks = remove_hyperlinks
        self._fix_check = fix_check
        self._contain_closest_title_levels = contain_closest_title_levels
        self._title_convert_to_markdown = title_convert_to_markdown
        self.TALK_RECORD = TALK_RECORD
        self.ADMISSION_RECORD = ADMISSION_RECORD
        self.SURGERY_CONSENT = SURGERY_CONSENT

    @staticmethod
    def convert_table_to_markdown(table) -> str:
        md = []
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            row_text = (
                "| " + " | ".join(cell.get_text(strip=True) for cell in cells) + " |"
            )
            md.append(row_text)

            if row.find("th"):
                header_sep = "| " + " | ".join("---" for _ in cells) + " |"
                md.append(header_sep)

        return "\n".join(md)

    def preprocessing(self, content: str) -> tuple:
        soup = BeautifulSoup(content, "html.parser")

        # clean hyperlinks
        if self._remove_hyperlinks:
            a_tags = soup.find_all("a")
            for tag in a_tags:
                text = tag.get_text()
                cleaned_text = text.replace("\n", " ").replace("\r", "")
                tag.replace_with(cleaned_text)

        # clean unchecked checkboxes and radio buttons
        if self._fix_check:
            match_inputs = soup.find_all("input", {"type": ["checkbox", "radio"]})
            for input_tag in match_inputs:
                if not input_tag.has_attr("checked"):
                    next_span = input_tag.find_next_sibling("span")
                    if next_span:
                        next_span.extract()
                    input_tag.extract()

        # split tables
        tables_md = []
        tables = soup.find_all("table")
        for table in tables:
            table_md = self.convert_table_to_markdown(table)
            tables_md.append(table_md)
            table.decompose()

        return str(soup), tables_md

    @staticmethod
    def convert_to_markdown(html_tag: str, title: str) -> str:
        if not (title and html_tag):
            return title

        html_tag = html_tag.lower()
        if html_tag.startswith("h") and html_tag[1:].isdigit():
            level = int(html_tag[1])
            return f'{"#" * level} {title}'
        else:
            return title

    def trans_titles_and_content(
        self, content: str, titles: list[tuple[str, str]]
    ) -> str:
        titles = titles[-self._contain_closest_title_levels :]
        if self._contain_closest_title_levels == 0:
            titles = []

        if not content:
            return content

        trans_content = ""
        for tag, title in titles:
            if not title:
                continue

            if self._title_convert_to_markdown:
                title = HtmlExtractor.convert_to_markdown(tag, title)

            trans_content += f"{title}\n"
        trans_content += content
        return trans_content

    def trans_meta_titles(self, titles: list[tuple[str, str]]):
        trans_titles = []
        for tag, title in titles:
            if not title:
                continue

            if self._title_convert_to_markdown:
                title = HtmlExtractor.convert_to_markdown(tag, title)

            trans_titles.append(title)
        return trans_titles
    
    def EMR_type_recognize(self, content: str) -> str:
        
        EMR_TYPES = {
            "谈话记录]": (self.TALK_RECORD, [
                ('table', '基本信息'), 
                ('table', '谈话记录')
                ]),
            "入院记录]": (self.ADMISSION_RECORD, [
                ('p', '主诉'),
                ('p', '现病史')
                ]),
            "入出院记录]": (self.ADMISSION_RECORD, [
                ('p', '主诉'), 
                ('p', '现病史')
                ]),
            "手术知情同意书]": (self.SURGERY_CONSENT, [
                ('p', '简要病情'),
                ('p', '术前诊断'),
                ('p', '拟实施手术名称'),
                ])
        }
        
        soup = BeautifulSoup(content, 'html.parser')
        header = soup.find('header')
        
        if not header:
            return False
        
        title_text = header.text.strip().replace(" ", "")
        
        def find_element(tag, data_name):
            return soup.find(tag, {'data-name': data_name}) or \
                soup.find(lambda t: t.name == tag and t.text.startswith(f'{data_name}：'))
        
        for key, (emr_type, required_elements) in EMR_TYPES.items():
            if key in title_text:
                if all(find_element(tag, data_name) for tag, data_name in required_elements):
                    return emr_type

        return False

    def extract(self, EMR_type: str = None) -> list[Document]:
        with open(
            self._file_path, "r", encoding=utils.get_encoding(self._file_path)
        ) as f:
            text = f.read()
            
            if EMR_type is None:
                EMR_type = self.EMR_type_recognize(text)
              
            # preprocess
            text, tables = self.preprocessing(text)

            html_doc = readability.Document(text)
            content, split_contents, titles = html_text.extract_text(
                html_doc.summary(html_partial=True), title=html_doc.title()
            )

            docs = []
            for content, hierarchy_titles in zip(split_contents, titles):
                docs.append(
                    Document(
                        page_content=self.trans_titles_and_content(
                            content, hierarchy_titles
                        ),
                        metadata={"titles": self.trans_meta_titles(hierarchy_titles)},
                    )
                )

            for table in tables:
                docs.append(Document(page_content=table))
            
            content = "\n".join(doc.page_content for doc in docs)
            return self.extract_by_type(EMR_type, docs, content)

        
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
