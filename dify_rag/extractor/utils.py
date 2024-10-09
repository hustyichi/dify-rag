import re

common_characters = set(
    "＞、abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:'\"-，。！？；：”“‘’\n\t+-*\\/·[]{}【】()（）@#$%^&<>《》`~］′＜～‐='"
)
# 添加希腊字母（小写和大写）
greek_letters = "αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
common_characters.update(greek_letters)
start_zh_ord, end_zh_ord = ord("一"), ord("龥")

all_codecs = [
    "utf-8",
    "gb2312",
    "gbk",
    "utf_16",
    "ascii",
    "big5",
    "big5hkscs",
    "cp037",
    "cp273",
    "cp424",
    "cp437",
    "cp500",
    "cp720",
    "cp737",
    "cp775",
    "cp850",
    "cp852",
    "cp855",
    "cp856",
    "cp857",
    "cp858",
    "cp860",
    "cp861",
    "cp862",
    "cp863",
    "cp864",
    "cp865",
    "cp866",
    "cp869",
    "cp874",
    "cp875",
    "cp932",
    "cp949",
    "cp950",
    "cp1006",
    "cp1026",
    "cp1125",
    "cp1140",
    "cp1250",
    "cp1251",
    "cp1252",
    "cp1253",
    "cp1254",
    "cp1255",
    "cp1256",
    "cp1257",
    "cp1258",
    "euc_jp",
    "euc_jis_2004",
    "euc_jisx0213",
    "euc_kr",
    "gb2312",
    "gb18030",
    "hz",
    "iso2022_jp",
    "iso2022_jp_1",
    "iso2022_jp_2",
    "iso2022_jp_2004",
    "iso2022_jp_3",
    "iso2022_jp_ext",
    "iso2022_kr",
    "latin_1",
    "iso8859_2",
    "iso8859_3",
    "iso8859_4",
    "iso8859_5",
    "iso8859_6",
    "iso8859_7",
    "iso8859_8",
    "iso8859_9",
    "iso8859_10",
    "iso8859_11",
    "iso8859_13",
    "iso8859_14",
    "iso8859_15",
    "iso8859_16",
    "johab",
    "koi8_r",
    "koi8_t",
    "koi8_u",
    "kz1048",
    "mac_cyrillic",
    "mac_greek",
    "mac_iceland",
    "mac_latin2",
    "mac_roman",
    "mac_turkish",
    "ptcp154",
    "shift_jis",
    "shift_jis_2004",
    "shift_jisx0213",
    "utf_32",
    "utf_32_be",
    "utf_32_le" "utf_16_be",
    "utf_16_le",
    "utf_7",
]


def find_codec(blob):
    global all_codecs
    for c in all_codecs:
        try:
            blob.decode(c)
            return c
        except Exception as e:
            pass

    return "utf-8"


def get_encoding(file) -> str:
    with open(file, "rb") as f:
        return find_codec(f.read())


def is_gibberish(text):
    text = sorted(text)
    check_char_list = list(text)
    check_result_list = list()
    for char in check_char_list:
        if char in common_characters or (start_zh_ord <= ord(char) <= end_zh_ord):
            check_result_list.append(True)
        else:
            check_result_list.append(False)
            if check_result_list.count(False) / len(check_result_list) > 0.3:
                return False
    return check_result_list.count(False) / len(check_result_list) < 0.3


def fix_error_pdf_content(text: str):
    # 替换空白字符
    text = text.replace("\xa0", "")
    text = text.replace("\u3000", " ")
    text = text.replace("\U001001b0", ".")
    # 匹配，和袁的映射
    text = text.replace("袁", "，")
    # 匹配。和 遥
    text = text.replace("遥", "。")
    # 匹配：和 院
    ## 如果院前面是医的话，那么就不用转换
    text = re.sub(r"(?<!医)院", "：", text)
    # 匹配（和 渊
    text = text.replace("渊", "（")
    # 匹配）和 冤
    text = text.replace("冤", "）")
    # 匹配、和尧
    text = text.replace("尧", "、")
    # 匹配【和 揖
    text = text.replace("揖", "【")
    # 匹配】和 铱
    text = text.replace("铱", "】")
    # 匹配℃ 和益 利用正则匹配了益字前面是否为数字，如果是数字那么才匹配
    # 注意识别出来的益和前面的数字之间有一个空格的
    text = re.sub(r"(?<=\d\s)益", "℃", text)
    # 匹配~和 耀
    text = text.replace("耀", "~")
    # 匹配；和 曰
    text = text.replace("曰", "；")

    text = re.sub(r"(\d)依", r"\1±", text)

    text = text.replace("滋g", "μg")

    text = re.sub(r"伊(\d+)", r"x\1", text)

    text = text.replace("覬", "∅")

    # 修复 《 和 》 解析异常
    text = re.sub(r"叶(.*?)曳", r"《\1》", text, flags=re.DOTALL)

    # 修复 ≤
    text = re.sub(r"逸(\d+)", r"≥", text)
    text = re.sub(r"臆(\d+)", r"≤", text)

    # 修复 -
    text = text.replace("鄄", "-")
    
    # 修复 ●
    text = text.replace("\uf06c", "●")

    # 修复 ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩
    text = re.sub(
        r"淤(.*?)于(.*?)盂(.*?)榆(.*?)虞(.*?)愚(.*?)舆(.*?)余(.*?)俞(.*?)逾",
        r"①\1②\2③\3④\4⑤\5⑥\6⑦\7⑧\8⑨\9⑩",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"淤(.*?)于(.*?)盂(.*?)榆(.*?)虞(.*?)愚(.*?)舆(.*?)余(.*?)俞",
        r"①\1②\2③\3④\4⑤\5⑥\6⑦\7⑧\8⑨",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"淤(.*?)于(.*?)盂(.*?)榆(.*?)虞(.*?)愚(.*?)舆(.*?)余",
        r"①\1②\2③\3④\4⑤\5⑥\6⑦\7⑧",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"淤(.*?)于(.*?)盂(.*?)榆(.*?)虞(.*?)愚(.*?)舆",
        r"①\1②\2③\3④\4⑤\5⑥\6⑦",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"淤(.*?)于(.*?)盂(.*?)榆(.*?)虞(.*?)愚",
        r"①\1②\2③\3④\4⑤\5⑥",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"淤(.*?)于(.*?)盂(.*?)榆(.*?)虞", r"①\1②\2③\3④\4⑤", text, flags=re.DOTALL
    )
    text = re.sub(r"淤(.*?)于(.*?)盂(.*?)榆", r"①\1②\2③\3④", text, flags=re.DOTALL)
    text = re.sub(r"淤(.*?)于(.*?)盂", r"①\1②\2③", text, flags=re.DOTALL)
    text = re.sub(r"淤(.*?)于", r"①\1②", text, flags=re.DOTALL)

    # 修复 [ 和 ] 解析异常
    text = re.sub(r"咱(.{0,30}?)暂", r"[\1]", text, flags=re.DOTALL)

    # 修复罗马数字字符
    text = re.sub(r"(?<![\u4e00-\u9fa5])玉|玉(?![\u4e00-\u9fa5])|玉(?=期)", "Ⅰ", text)
    text = re.sub(r"(?<![\u4e00-\u9fa5])域|域(?![\u4e00-\u9fa5])|域(?=期)", "Ⅱ", text)
    text = re.sub(r"(?<![\u4e00-\u9fa5])芋|芋(?![\u4e00-\u9fa5])|芋(?=期)", "Ⅲ", text)
    text = re.sub(r"(?<![\u4e00-\u9fa5])郁|郁(?![\u4e00-\u9fa5])|郁(?=期)", "Ⅳ", text)

    return text.replace("\n", "")
