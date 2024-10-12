# -*- coding: utf-8 -*-
import copy
import enum
import re

import lxml
import lxml.etree
from lxml.html.clean import Cleaner

from dify_rag.extractor.html import constants


class SupType(enum.Enum):
    UNKNOWN = "unknown"
    NUMERAL = "numeral"
    QUOTE = "quote"


NEWLINE_TAGS = frozenset(
    [
        "article",
        "aside",
        "br",
        "dd",
        "details",
        "div",
        "dt",
        "fieldset",
        "figcaption",
        "footer",
        "form",
        "header",
        "hr",
        "legend",
        "li",
        "main",
        "nav",
        "table",
        "tr",
    ]
)
DOUBLE_NEWLINE_TAGS = frozenset(
    [
        "blockquote",
        "dl",
        "figure",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ol",
        "p",
        "pre",
        "title",
        "ul",
    ]
)

SPLIT_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
]

cleaner = Cleaner(
    scripts=True,
    javascript=False,  # onclick attributes are fine
    comments=True,
    style=True,
    links=True,
    meta=True,
    page_structure=False,  # <title> may be nice to have
    processing_instructions=True,
    embedded=True,
    frames=True,
    forms=False,  # keep forms
    annoying_tags=False,
    remove_unknown_tags=False,
    safe_attrs_only=False,
)


def _cleaned_html_tree(html):
    if isinstance(html, lxml.html.HtmlElement):
        tree = html
    else:
        tree = parse_html(html)

    # we need this as https://bugs.launchpad.net/lxml/+bug/1838497
    try:
        cleaned = cleaner.clean_html(tree)
    except AssertionError:
        cleaned = tree

    return cleaned


def parse_html(html):
    """Create an lxml.html.HtmlElement from a string with html.
    XXX: mostly copy-pasted from parsel.selector.create_root_node
    """
    body = html.strip().replace("\x00", "").encode("utf8") or b"<html/>"
    parser = lxml.html.HTMLParser(recover=True, encoding="utf8")
    root = lxml.etree.fromstring(body, parser=parser)
    if root is None:
        root = lxml.etree.fromstring(b"<html/>", parser=parser)
    return root


_whitespace = re.compile(r"\s+")
_has_trailing_whitespace = re.compile(r"\s$").search
_has_punct_after = re.compile(r'^[,:;.!?")]').search
_has_open_bracket_before = re.compile(r"\($").search


def _normalize_whitespace(text):
    return _whitespace.sub(" ", text.strip())


def etree_to_text(
    tree,
    guess_punct_space=True,
    guess_layout=True,
    newline_tags=NEWLINE_TAGS,
    double_newline_tags=DOUBLE_NEWLINE_TAGS,
    split_tags=SPLIT_TAGS,
    title=None,
):
    """
    Convert a html tree to text. Tree should be cleaned with
    ``html_text.html_text.cleaner.clean_html`` before passing to this
    function.

    See html_text.extract_text docstring for description of the
    approach and options.
    """
    chunks = []
    split_chunks = []
    split_texts = []
    split_texts_hierarch_titles = []
    current_hierarchy_titles = []
    if title and title != constants.NO_TITLE:
        current_hierarchy_titles.append((constants.TITLE_KEY, title))

    _NEWLINE = object()
    _DOUBLE_NEWLINE = object()
    prev = _DOUBLE_NEWLINE  # _NEWLINE, _DOUBLE_NEWLINE or content of the previous chunk (str)

    def check_sup_type(text, tag=None) -> SupType:
        if not (tag and tag == "sup"):
            return SupType.UNKNOWN

        text = text.replace(" ", "")
        QUOTE_PATTERN = r"^\[\s*(\d+|(\d+\s*[-～]\s*\d+))(?:[\s,，]\s*(\d+|(\d+\s*[-～]\s*\d+)))*\s*\]$"

        if text.isdigit():
            return SupType.NUMERAL
        elif re.match(QUOTE_PATTERN, text):
            return SupType.QUOTE

        return SupType.UNKNOWN

    def should_add_space(text, tag=None):
        """Return True if extra whitespace should be added before text"""
        if prev in {_NEWLINE, _DOUBLE_NEWLINE}:
            return False
        if not guess_punct_space:
            return True
        if not _has_trailing_whitespace(prev):
            if (
                _has_punct_after(text)
                or _has_open_bracket_before(prev)
                or check_sup_type(text, tag) == SupType.NUMERAL
            ):
                return False
        return True

    def get_space_between(text, tag=None):
        if not text:
            return " "
        return " " if should_add_space(text, tag) else ""

    def add_newlines(tag):
        nonlocal prev
        if not guess_layout:
            return
        if prev is _DOUBLE_NEWLINE:  # don't output more than 1 blank line
            return
        if tag in double_newline_tags:
            chunks.append("\n" if prev is _NEWLINE else "\n\n")
            split_chunks.append("\n" if prev is _NEWLINE else "\n\n")
            prev = _DOUBLE_NEWLINE
        elif tag in newline_tags:
            if prev is not _NEWLINE:
                chunks.append("\n")
                split_chunks.append("\n")
            prev = _NEWLINE

    def add_text(text_content, tag=None):
        nonlocal prev
        text = _normalize_whitespace(text_content) if text_content else ""
        if not text:
            return

        space = get_space_between(text, tag)

        sup_type = check_sup_type(text, tag)
        if sup_type == SupType.QUOTE:
            return
        elif sup_type == SupType.NUMERAL:
            text = f"^{text}"

        chunks.extend([space, text])
        # ignore header title
        if not (tag and tag in split_tags):
            split_chunks.extend([space, text])

        prev = text_content

    def compare_html_tags(tag1, tag2):
        level1 = constants.TAG_HIERARCHY.get(tag1.lower(), 0)
        level2 = constants.TAG_HIERARCHY.get(tag2.lower(), 0)

        if level1 > level2:
            return 1
        elif level1 < level2:
            return -1
        else:
            return 0

    def update_current_hierarchy_titles(tag=None, text=None):
        nonlocal current_hierarchy_titles

        if (not tag) or (not text) or (tag not in split_tags):
            return

        while (
            current_hierarchy_titles
            and compare_html_tags(current_hierarchy_titles[-1][0], tag) <= 0
        ):
            current_hierarchy_titles.pop()

        current_hierarchy_titles.append((tag.strip(), text.strip()))

    def check_add_add_split_texts(tag=None, text=None):
        nonlocal split_texts
        nonlocal split_chunks

        if tag and (tag not in split_tags):
            return

        prev_text = "".join(split_chunks).strip()
        if prev_text:
            split_texts.append(prev_text)
            split_texts_hierarch_titles.append(copy.deepcopy(current_hierarchy_titles))

        update_current_hierarchy_titles(tag, text)
        split_chunks = []

    # Extract text from the ``tree``: fill ``chunks`` variable
    for event, el in lxml.etree.iterwalk(tree, events=("start", "end")):
        if event == "start":
            check_add_add_split_texts(el.tag, el.text)
            add_newlines(el.tag)
            add_text(el.text, el.tag)
        elif event == "end":
            add_newlines(el.tag)
            if el is not tree:
                add_text(el.tail, el.tag)

    check_add_add_split_texts()

    return "".join(chunks).strip(), split_texts, split_texts_hierarch_titles


def selector_to_text(sel, guess_punct_space=True, guess_layout=True):
    """Convert a cleaned parsel.Selector to text.
    See html_text.extract_text docstring for description of the approach
    and options.
    """
    import parsel

    if isinstance(sel, parsel.SelectorList):
        # if selecting a specific xpath
        text = []
        for s in sel:
            extracted = etree_to_text(
                s.root, guess_punct_space=guess_punct_space, guess_layout=guess_layout
            )
            if extracted:
                text.append(extracted)
        return " ".join(text)
    else:
        return etree_to_text(
            sel.root, guess_punct_space=guess_punct_space, guess_layout=guess_layout
        )


def cleaned_selector(html):
    """Clean parsel.selector."""
    import parsel

    try:
        tree = _cleaned_html_tree(html)
        sel = parsel.Selector(root=tree, type="html")
    except (
        lxml.etree.XMLSyntaxError,
        lxml.etree.ParseError,
        lxml.etree.ParserError,
        UnicodeEncodeError,
    ):
        # likely plain text
        sel = parsel.Selector(html)
    return sel


def extract_text(
    html,
    guess_punct_space=True,
    guess_layout=True,
    newline_tags=NEWLINE_TAGS,
    double_newline_tags=DOUBLE_NEWLINE_TAGS,
    split_tags=SPLIT_TAGS,
    title=None,
):
    """
    Convert html to text, cleaning invisible content such as styles.

    Almost the same as normalize-space xpath, but this also
    adds spaces between inline elements (like <span>) which are
    often used as block elements in html markup, and adds appropriate
    newlines to make output better formatted.

    html should be a unicode string or an already parsed lxml.html element.

    ``html_text.etree_to_text`` is a lower-level function which only accepts
    an already parsed lxml.html Element, and is not doing html cleaning itself.

    When guess_punct_space is True (default), no extra whitespace is added
    for punctuation. This has a slight (around 10%) performance overhead
    and is just a heuristic.

    When guess_layout is True (default), a newline is added
    before and after ``newline_tags`` and two newlines are added before
    and after ``double_newline_tags``. This heuristic makes the extracted
    text more similar to how it is rendered in the browser.

    Default newline and double newline tags can be found in
    `html_text.NEWLINE_TAGS` and `html_text.DOUBLE_NEWLINE_TAGS`.
    """
    if html is None:
        return ""
    no_content_nodes = (lxml.html.HtmlComment, lxml.html.HtmlProcessingInstruction)
    if isinstance(html, no_content_nodes):
        return ""
    cleaned = _cleaned_html_tree(html)
    return etree_to_text(
        cleaned,
        guess_punct_space=guess_punct_space,
        guess_layout=guess_layout,
        newline_tags=newline_tags,
        double_newline_tags=double_newline_tags,
        split_tags=split_tags,
        title=title,
    )
