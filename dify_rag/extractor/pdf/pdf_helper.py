from collections import Counter

from dify_rag.extractor.utils import is_gibberish


def get_lines(page_blocks):
    lines = []
    lines_page_idx = []
    for page_idx, text_blocks in enumerate(page_blocks):
        for block in text_blocks:
            block_text = block[4]
            if is_gibberish(block_text):
                lines.append(block_text.replace("\n", ""))
                lines_page_idx.append(page_idx)
    return lines, lines_page_idx

def collect_page_metrics(page):
    """收集单页的页眉页脚度量数据"""
    text_blocks = page.get_text("blocks")
    if not text_blocks:
        return None

    header_y, footer_y = float('inf'), float('-inf')
    header_idx, footer_idx = -1, -1
    header_height, footer_height = 0, 0

    for idx, block in enumerate(text_blocks):
        _, y0, _, y1, *_ = block
        if y0 < header_y:
            header_y, header_idx, header_height = y0, idx, y1 - y0
        if y1 > footer_y:
            footer_y, footer_idx, footer_height = y1, idx, y1 - y0

    return {
        'text_blocks': text_blocks,
        'header_idx': header_idx,
        'footer_idx': footer_idx,
        'header_height': header_height,
        'footer_height': footer_height
    }

def should_remove_headers_footers(page_metrics, threshold=0.9):
    """判断是否应该移除页眉页脚"""
    if not page_metrics:
        return False, False

    header_heights = [m['header_height'] for m in page_metrics if m]
    footer_heights = [m['footer_height'] for m in page_metrics if m]

    def exists_common_height(heights):
        if not heights:
            return False
        _, count = Counter(heights).most_common(1)[0]
        return count / len(heights) >= threshold

    return exists_common_height(header_heights), exists_common_height(footer_heights)

def filter_doc_header_or_footer(doc):
    """
    过滤文档中的页眉页脚
    页眉和页脚，每页都应该具备且格式相同
    """
    page_metrics = [collect_page_metrics(page) for page in doc]

    header_exists, footer_exists = should_remove_headers_footers(page_metrics)

    if not header_exists and not footer_exists:
        return [m['text_blocks'] for m in page_metrics if m]

    filtered_page_blocks = []
    for metrics in page_metrics:
        if not metrics:
            continue

        indices_to_remove = []
        if header_exists and metrics['header_idx'] != -1:
            indices_to_remove.append(metrics['header_idx'])
        if footer_exists and metrics['footer_idx'] != -1:
            indices_to_remove.append(metrics['footer_idx'])

        filtered_blocks = [
            block for idx, block in enumerate(metrics['text_blocks'])
            if idx not in indices_to_remove
        ]
        filtered_page_blocks.append(filtered_blocks)

    return filtered_page_blocks

def get_lines_toc(toc, lines, lines_page_idx):
    """获取TOC的行索引"""
    lines_toc = []
    for level, title, page in toc:
        # 在目标页中查找包含该标题的行
        title_line_idx = next(
            (i for i, idx in enumerate(lines_page_idx)
                if idx == page - 1 and
                (title in lines[i] or title.replace(" ", "") in lines[i])),
            None
            )
        if title_line_idx is not None:
            lines_toc.append((level, title, title_line_idx))
    return lines_toc
