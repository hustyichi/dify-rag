from abc import ABC
from enum import Enum
from typing import ClassVar, Dict, List


class EMRType(Enum):
    TALK_RECORD = "谈话记录"
    ADMISSION_RECORD = "入院记录"
    SURGERY_CONSENT = "手术知情同意书"

class EMRConstants:
    EMR_TYPE_KEY = "emr_type"
    GENDER_KEY = "gender"
    AGE_KEY = "age"
    DEPARTMENT_KEY = "department"
    MEDICAL_RECORD_NUMBER_KEY = "medical_record_number"
    DIAGNOSIS_KEY = "diagnosis"
    TREATMENT_KEY = "treatment"
    INITIAL_DIAGNOSIS_KEY = "初步诊断"
    SUPPLEMENTARY_DIAGNOSIS_KEY = "补充诊断"
    REVISED_DIAGNOSIS_KEY = "修正诊断"
    TREATMENT_PLAN_KEY = "诊疗方案"
    PROCEDURE_KEY = "拟实施手术名称"
    
    BASIC_FIELDS_MAPPING = {
        "性别": GENDER_KEY,
        "年龄": AGE_KEY,
        "科室": DEPARTMENT_KEY,
        "病案号": MEDICAL_RECORD_NUMBER_KEY,
    }
    
    BASIC_INFO_TITLE = "基本信息"
    BASIC_INFO_TOC = [
        "性别",
        "年龄",
        "科室",
        "病案号",
    ]
    
    BASIC_METADATA: Dict[str, str] = {
        EMR_TYPE_KEY: "",
        GENDER_KEY: "",
        AGE_KEY: "",
        DEPARTMENT_KEY: "",
        MEDICAL_RECORD_NUMBER_KEY: "",
        DIAGNOSIS_KEY: "",
        TREATMENT_KEY: "",
    }

    MIN_CONTENT_LENGTH = 100

class BaseEMRConfig(ABC):
    EMR_TYPE: ClassVar[EMRType]
    HEADERS: ClassVar[List[str]]
    REQUIRED_ELEMENTS: ClassVar[List[Dict[str, str]]]
    BASIC_FIELDS: ClassVar[List[str]]
    EXTRACT_FIELDS: ClassVar[List[str]]
    TOC_ITEMS: ClassVar[List[str]]

    @classmethod
    def is_applicable(cls, file_path: str) -> bool:
        return any(header in file_path for header in cls.HEADERS)

class TalkRecordConfig(BaseEMRConfig):
    EMR_TYPE = "谈话记录"
    HEADERS = ["谈话记录]"]
    REQUIRED_ELEMENTS = [
        {
            "tag": "table", 
            "data_id": "谈话基本信息", 
            "data_name": "基本信息", 
            "keyword": "基本信息"
        },
        {
            "tag": "table", 
            "data_id": "谈话记录", 
            "data_name": "谈话记录", 
            "keyword": "谈话记录"
        }
    ]
    TALK_RECORD_PATTERN = r'谈话记录.*?\| \[(.*?)\] \|'
    EXTRACT_FIELDS = []
    TOC_ITEMS = [
        "谈话记录"
    ]

class AdmissionRecordConfig(BaseEMRConfig):
    EMR_TYPE = "入院记录"
    HEADERS = ["入院记录]", "入出院记录]"]
    REQUIRED_ELEMENTS = [
        {
            "tag": "p",
            "data_id": "主诉",
            "data_name": "主诉",
            "keyword": "主诉"
        },
        {
            "tag": "p",
            "data_id": "现病史",
            "data_name": "现病史",
            "keyword": "现病史"
        }
    ]
    DIAGNOSIS_START = "| 初步诊断"
    INITIAL_DIAGNOSIS_PATTERN = r'\| 初步诊断：.*?\| \[(.*?)\] \|'
    INITIAL_DIAGNOSIS_KEY = "初步诊断"
    REVISED_DIAGNOSIS_PATTERN = r'修正诊断：([\d\.、、\w\W]+?)(?:医师签名|签名时间|\]|$)'
    REVISED_DIAGNOSIS_KEY = "修正诊断"
    SUPPLEMENTARY_DIAGNOSIS_PATTERN = r'补充诊断：([\d\.、、\w\W]+?)(?:医师签名|签名时间|\]|$)'
    SUPPLEMENTARY_DIAGNOSIS_KEY = "补充诊断"
    DIAGNOSIS_CLEAN_PATTERN = r'[^\u4e00-\u9fa5\d\.、]+'
    EXTRACT_FIELDS = [
        "主诉",
        "现病史",
        "流行病学史",
        "既往史",
        "个人史",
        "婚育史",
        "家族史",
        # "辅助检查"
    ]
    TOC_ITEMS = [
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
        "补充诊断",
        "修正诊断",
        "诊疗方案"
    ]

class SurgeryConsentConfig(BaseEMRConfig):
    EMR_TYPE = "手术知情同意书"
    HEADERS = ["手术知情同意书]"]
    REQUIRED_ELEMENTS = [
        {
            "tag": "p",
            "data_id": "手术知情病历摘要", 
            "data_name": "简要病情", 
            "keyword": "简要病情"
        },
        {
            "tag": "p", 
            "data_id": "手术知情诊断信息", 
            "data_name": "术前诊断", 
            "keyword": "术前诊断"
        },
        {
            "tag": "p", 
            "data_id": "手术知情拟手术名称", 
            "data_name": "拟实施手术名称", 
            "keyword": "拟实施手术名称"
        }
    ]
    EXTRACT_FIELDS = [
        "术中、术后可能出现的各种情况、意外、风险及并发症",
        "针对上述情况，医师根据医疗规范采取在术前、术中、术后预防及治疗措施",
    ]
    TOC_ITEMS = [
            "简要病情",
            "术前诊断",
            "拟实施手术名称",
            "拟实施麻醉方式",
            "手术指征",
            "手术禁忌症",
            "术前准备",
            # "术中、术后可能出现的各种情况、意外、风险及并发症",
            # "针对上述情况，医师根据医疗规范采取在术前、术中、术后预防及治疗措施"
        ]

class EMRConfigFactory:
    @staticmethod
    def create_config(emr_type: EMRType) -> BaseEMRConfig:
        config_map = {
            EMRType.TALK_RECORD: TalkRecordConfig,
            EMRType.ADMISSION_RECORD: AdmissionRecordConfig,
            EMRType.SURGERY_CONSENT: SurgeryConsentConfig,
        }
        config_class = config_map.get(emr_type)
        if config_class is None:
            raise ValueError(f"Unsupported EMR type: {emr_type}")
        config = config_class()
        return config