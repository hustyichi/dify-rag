import chardet


def get_encoding(file) -> str:
    with open(file, "rb") as f:
        tmp = chardet.detect(f.read())
        return tmp["encoding"] or "utf-8"
