from dify_rag.extractor.markdown_extractor import MarkdownExtractor
from tests.log import logger

file_path = "tests/data/多模态摘要生成.md"


def test_markdown_extractor():
    extractor = MarkdownExtractor(file_path)
    text_docs = extractor.extract()
    for d in text_docs:
        assert d.metadata
        assert d.page_content

        logger.info("----->")
        logger.info(f"Metadata: {d.metadata}")
        logger.info(f"{d.page_content} ({len(d.page_content)})")


if __name__ == "__main__":
    test_markdown_extractor()
