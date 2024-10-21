TALK_RECORD = "谈话记录"
ADMISSION_RECORD = "入院记录"
SURGERY_CONSENT = "手术知情同意书"
BASIC_FIELDS = [
    "性别",
    "年龄",
    "科室",
    "床号",
    "病案号",
]

class BaseEMRConfig:
    RECORD_TYPE: str
    HEADERS: list[str]
    REQUIRED_ELEMENTS: list[dict[str, str]]
    BASIC_FIELDS: list[str]
    EXTRACT_FIELDS: list[str]
    TOC_ITEMS: list[str]

    @classmethod
    def is_applicable(cls, file_path: str) -> bool:
        return any(header in file_path for header in cls.HEADERS)

class TalkRecordConfig(BaseEMRConfig):
    RECORD_TYPE = "谈话记录"
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
    BASIC_FIELDS = BASIC_FIELDS
    TALK_RECORD_PATTERN = r'谈话记录.*?\| \[(.*?)\] \|'
    EXTRACT_FIELDS = []
    TOC_ITEMS = [
        "谈话记录"
    ]

class AdmissionRecordConfig(BaseEMRConfig):
    RECORD_TYPE = "入院记录"
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
    BASIC_FIELDS = BASIC_FIELDS
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
    RECORD_TYPE = "手术知情同意书"
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
    BASIC_FIELDS = BASIC_FIELDS
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

EMR_CONFIGS = {
    TalkRecordConfig.RECORD_TYPE: TalkRecordConfig,
    AdmissionRecordConfig.RECORD_TYPE: AdmissionRecordConfig,
    SurgeryConsentConfig.RECORD_TYPE: SurgeryConsentConfig
}