from dify_rag.extractor.epub_extractor import EpubExtractor
from tests.log import logger

file_path = "tests/data/sample_test.epub"

def test_epub_extractor():
    extractor = EpubExtractor(file_path)
    text_docs = extractor.extract()

    for d in text_docs:
        assert d.metadata
        assert d.page_content

        logger.info("----->")
        logger.info(f"Metadata: {d.metadata}")
        logger.info(f"{d.page_content} ({len(d.page_content)})")


if __name__ == "__main__":
    test_epub_extractor()