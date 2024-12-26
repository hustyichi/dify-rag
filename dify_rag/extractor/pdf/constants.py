SUMMARY_KEYWORDS = [
    'introduction', 'abstract', 'keywords?', 'contents',
    '摘要', '引言', '关键词', '前言', '目录'
]

SUMMARY_PATTERN = fr"^[0-9. 一、i]*({'|'.join(k.replace('', r'\s*') for k in SUMMARY_KEYWORDS)})"

TITLE_PATTERN = [
    SUMMARY_PATTERN,
    r"^第[零一二三四五六七八九十百0-9]+(分?编|部分)",
    r"^第[零一二三四五六七八九十百0-9]+章",
    r"^第[零一二三四五六七八九十百0-9]+节",
    r"^第[零一二三四五六七八九十百0-9]+条",
    r"^第[0-9]+章",
    r"^第[0-9]+节",
    r"^[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}[\.、](?=\S|$)",
    r"^[0-9]{1,2}\.[0-9]{1,2}\.[0-9]{1,2}[\.、](?=\S|$)",
    r"^[0-9]{1,2}\.[0-9]{1,2}[\.、](?=\S|$)",
    r"^[0-9]{1,2}[\.、](?!\d)(\S+)",
    r"^[\(（【［\[][零一二三四五六七八九十百]+[\)）】］\]]",
    # r"^[\(（【][0-9]{1,2}?[\)）】]",
    r"^[零一二三四五六七八九十百]+[\.。:：、]",
    r"^PART (ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|TEN)",
    r"^Chapter (I+V?|VI*|XI|IX|X)",
    r"^Section [0-9]+",
    r"^Article [0-9]+"
]

MAX_WORD_COUNT = 10
MAX_CHAR_COUNT = 20

SPLIT_TAGS = [1, 2, 3]