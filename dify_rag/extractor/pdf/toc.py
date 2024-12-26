import re
from typing import Optional

from dify_rag.extractor.pdf import constants


def extract_title(text: str) -> Optional[dict[str, str]]:
    """匹配标题并返回标题及其对应的正则匹配模式"""
    text = text.strip()
    if not text:
        return None

    words = text.split()
    if len(words) > constants.MAX_WORD_COUNT:
        return None
    if re.search(r'[\u4e00-\u9fff]', text) and len(text) >= constants.MAX_CHAR_COUNT:
        return None

    for pattern in constants.TITLE_PATTERN:
        pattern = re.compile(pattern)
        match = pattern.match(text)
        if match:
            matched_text = match.group(0)
            # 如果匹配的文本后面紧跟着标点符号，不视为标题
            remaining_text = text[len(matched_text):].strip()
            if remaining_text and re.search(r'[，,。：:；;!！?？]', remaining_text) and len(remaining_text) > 2:
                return None
            return {
                'text': text,
                'pattern': pattern.pattern
            }
    return None

def is_summary(title: dict) -> bool:
    """判断给定的模式是否为摘要模式"""
    return title['pattern'] == constants.SUMMARY_PATTERN if constants.SUMMARY_PATTERN else False

def generate_toc(lines: list[str]) -> list[list]:
    """生成目录结构"""
    toc = []
    pattern_order = []
    stack = []
    level = None
    
    # 提取所有标题
    titles = []
    for i, line in enumerate(lines):
        title_info = extract_title(line)
        if title_info:
            title_info['line_number'] = i
            titles.append(title_info)

    # 构建 pattern_order
    for title in titles:
        if title['pattern'] not in pattern_order and not is_summary(title):
            pattern_order.append(title['pattern'])

    # 构建层级树并生成 TOC
    for title in titles:

        if is_summary(title):
            # 摘要作为顶层标题
            if level is None:
                level = 1
            toc.append([level, title['text'], title['line_number']])
            continue

        current_level = pattern_order.index(title['pattern'])

        # 根据栈顶元素判断当前标题的层级
        while stack:
            top_level = pattern_order.index(stack[-1]['pattern'])
            if current_level > top_level:
                level = top_level + 1
                break
            else:
                stack.pop()
        else:
            level = 1

        # 如果栈不为空，当前层级基于父层级
        if stack:
            level = pattern_order.index(title['pattern']) - pattern_order.index(stack[-1]['pattern']) + 1
        else:
            level = 1

        toc.append([level, title['text'], title['line_number']])

        stack.append(title)

    return toc