import chardet

common_characters = set(
    "＞、abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?;:'\"-，。！？；：”“‘’\n\t+-*\\/·[]{}【】()（）@#$%^&<>《》`~］′＜～‐='"
)
start_zh_ord, end_zh_ord = ord("一"), ord("龥")


def get_encoding(file) -> str:
    with open(file, "rb") as f:
        tmp = chardet.detect(f.read())
        return tmp["encoding"] or "utf-8"


def is_gibberish(text):
    text = sorted(text)
    text_length = len(text)
    check_char_list = list(text)
    check_result_list = list()
    if text_length > 2:
        # 采取抽检的方式
        check_char_list = [text[0], text[-1], text[text_length // 2]]
    for char in check_char_list:
        if char in common_characters or (start_zh_ord <= ord(char) <= end_zh_ord):
            check_result_list.append(True)
        else:
            check_result_list.append(False)
    return all(check_result_list)
