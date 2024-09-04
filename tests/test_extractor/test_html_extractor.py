from dify_rag.extractor.html_extractor import HtmlExtractor
from tests.log import logger

file_path = "tests/data/《中国产科麻醉专家共识 (2017) 》解读.html"


def test_html_extractor():
    extractor = HtmlExtractor(file_path)
    text_docs = extractor.extract()
    for d in text_docs:
        assert d.metadata
        assert d.page_content

        logger.info("----->")
        logger.info(f"Metadata: {d.metadata}")
        logger.info(f"{d.page_content} ({len(d.page_content)})")


if __name__ == "__main__":
    test_html_extractor()
