import re
from functools import lru_cache

import jieba

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

@lru_cache(maxsize=2048)
def get_word_segments(context: str):
    return list(jieba.cut(context, cut_all=True))

@lru_cache(maxsize=4096)
def should_protect_char(context: str, char: str) -> bool:
    return any(len(word) > 1 for word in get_word_segments(context) if char in word)

def create_replace_func(text: str, conversion_rules: dict):
    def replace_func(match):
        char = match.group(0)
        pos = match.start()
        context = text[max(0, pos - 3):min(len(text), pos + 4)]
        return char if should_protect_char(context, char) else conversion_rules[char]
    return replace_func

MAX_MATCH_LENGTH = 500
CIRCLE_NUMBERS_MAP = {
    "淤": "①", "于": "②", "盂": "③", "榆": "④", "虞": "⑤",
    "愚": "⑥", "舆": "⑦", "余": "⑧", "俞": "⑨", "逾": "⑩"
}

def fix_error_pdf_content(text: str):
    # 替换空白字符
    text = text.replace("\xa0", "")
    text = text.replace("\u2002", "")
    text = text.replace("\u2003", " ")
    text = text.replace("\u3000", " ")
    text = text.replace("\U001001b0", ".")

    conversion_rules = {
        "袁": "，",
        "遥": "。",
        "院": "：",
        "渊": "（",
        "冤": "）",
        "尧": "、",
        "揖": "【",
        "铱": "】",
        "耀": "~",
        "曰": "；",
        "鄄": "-",
        "覬": "∅",
    }
    pattern = re.compile('|'.join(map(re.escape, conversion_rules.keys())))

    replace_func = create_replace_func(text, conversion_rules)
    text = pattern.sub(replace_func, text)

    # 匹配℃ 和益 利用正则匹配了益字前面是否为数字，如果是数字那么才匹配
    # 注意识别出来的益和前面的数字之间有一个空格的
    text = re.sub(r"(?<=\d\s)益", "℃", text)

    text = re.sub(r"(\d)依", r"\1±", text)

    text = text.replace("滋g", "μg")

    text = re.sub(r"伊(\d+)", r"x\1", text)

    # 修复 《 和 》 解析异常
    text = re.sub(r"叶(.*?)曳", r"《\1》", text, flags=re.DOTALL)

    # 修复 ≤
    text = re.sub(r"逸(\d+)", r"≥", text)
    text = re.sub(r"臆(\d+)", r"≤", text)

    # 修复 ●
    text = text.replace("\uf06c", "●")

    # 修复 ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩
    circle_numbers_chars = list(CIRCLE_NUMBERS_MAP.keys())
    for i in range(len(circle_numbers_chars), 1, -1):
        pattern = ''.join([f"{c}(.{{0,{MAX_MATCH_LENGTH}}}?)" for c in circle_numbers_chars[:i-1]]) + circle_numbers_chars[i-1]
        replacement = ''.join([f"{CIRCLE_NUMBERS_MAP[c]}\\{j}" for j, c in enumerate(circle_numbers_chars[:i-1], 1)]) + CIRCLE_NUMBERS_MAP[circle_numbers_chars[i-1]]
        text = re.sub(pattern, replacement, text, flags=re.DOTALL)

    # 修复 [ 和 ] 解析异常
    text = re.sub(r"咱(.{0,30}?)暂", r"[\1]", text, flags=re.DOTALL)

    # 修复罗马数字字符
    text = re.sub(r"(?<![\u4e00-\u9fa5])玉|玉(?![\u4e00-\u9fa5])|玉(?=期)", "Ⅰ", text)
    text = re.sub(r"(?<![\u4e00-\u9fa5])域|域(?![\u4e00-\u9fa5])|域(?=期)", "Ⅱ", text)
    text = re.sub(r"(?<![\u4e00-\u9fa5])芋|芋(?![\u4e00-\u9fa5])|芋(?=期)", "Ⅲ", text)
    text = re.sub(r"(?<![\u4e00-\u9fa5])郁|郁(?![\u4e00-\u9fa5])|郁(?=期)", "Ⅳ", text)

    return text.replace("\n", "")
