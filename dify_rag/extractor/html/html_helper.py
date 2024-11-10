import copy
import re

from bs4 import BeautifulSoup

from dify_rag.extractor.html import constants


def convert_table_to_markdown(table) -> str:
    md = []
    rows = table.find_all("tr")
    first_row = True

    for row in rows:
        cells = row.find_all(["th", "td"])
        row_text = "| " + " | ".join(cell.get_text(strip=True) for cell in cells) + " |"
        md.append(row_text)

        if row.find("th") or first_row:
            header_sep = "| " + " | ".join("---" for _ in cells) + " |"
            md.append(header_sep)
            first_row = False

    return "\n".join(md)


def recursive_preprocess_tables(soup: BeautifulSoup, title: str) -> list:
    table_with_titles = []
    title_stack = []
    if title and title != constants.NO_TITLE:
        title_stack.append((constants.TITLE_KEY, title))

    match_tags = [
        key for key in constants.TAG_HIERARCHY.keys() if key != constants.TITLE_KEY
    ] + ["table"]
    for tag in soup.find_all(match_tags):

        if tag.name in constants.TAG_HIERARCHY:
            level = constants.TAG_HIERARCHY[tag.name]
            title_text = tag.get_text(strip=True)

            while title_stack and constants.TAG_HIERARCHY[title_stack[-1][0]] <= level:
                title_stack.pop()

            title_stack.append((tag.name, title_text))

        elif tag.name == "table":
            table_md = convert_table_to_markdown(tag)
            tag.decompose()

            table_with_titles.append(
                {"table": table_md, "titles": copy.deepcopy(title_stack)}
            )

    return table_with_titles


def preprocessing(
    content: str,
    title: str,
    use_first_header_as_title: bool = False,
    remove_hyperlinks: bool = True,
    fix_check: bool = True,
    seperate_tables: bool = True,
    prevent_duplicate_header: bool = True,
) -> tuple:
    soup = BeautifulSoup(content, "html.parser")

    header = soup.find(["h1", "h2"])
    if header and use_first_header_as_title:
        title = header.get_text().strip()
        if prevent_duplicate_header:
            header.extract()

    # clean header contents
    for tag in soup.find_all(re.compile("^h[1-6]$")):
        tag_text = tag.get_text()
        tag.clear()
        tag.string = tag_text.replace("\n", " ").replace("\r", "")

    # clean hyperlinks
    if remove_hyperlinks:
        a_tags = soup.find_all("a")
        for tag in a_tags:
            text = tag.get_text()
            cleaned_text = text.replace("\n", " ").replace("\r", "")
            tag.replace_with(cleaned_text)

    # clean unchecked checkboxes and radio buttons
    if fix_check:
        match_inputs = soup.find_all("input", {"type": ["checkbox", "radio"]})
        for input_tag in match_inputs:
            if not input_tag.has_attr("checked"):
                next_span = input_tag.find_next_sibling("span")
                if next_span:
                    next_span.extract()
                input_tag.extract()

    tables = []
    if seperate_tables:
        tables = recursive_preprocess_tables(soup, title)
    return str(soup), tables, title


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
    content: str,
    titles: list[tuple[str, str]],
    contain_closest_title_levels: int,
    title_convert_to_markdown: bool,
) -> str:
    titles = titles[-contain_closest_title_levels:]
    if contain_closest_title_levels == 0:
        titles = []

    if not content:
        return content

    trans_content = ""
    for tag, title in titles:
        if not title:
            continue

        if title_convert_to_markdown:
            title = convert_to_markdown(tag, title)

        trans_content += f"{title}\n"
    trans_content += content
    return trans_content


def trans_meta_titles(titles: list[tuple[str, str]], title_convert_to_markdown: bool):
    trans_titles = []
    for tag, title in titles:
        if not title:
            continue

        if title_convert_to_markdown:
            title = convert_to_markdown(tag, title)

        trans_titles.append(title)
    return trans_titles
