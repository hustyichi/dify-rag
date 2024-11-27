from dify_rag.extractor.word_extractor import WordExtractor
from tests.log import logger

file_path = "tests/data/大模型应用服务器配置.docx"


def test_word_extractor():
    extractor = WordExtractor(file_path)
    text_docs = extractor.extract()
    for d in text_docs:
        assert d.metadata
        assert d.page_content

        logger.info("----->")
        logger.info(f"Metadata: {d.metadata}")
        logger.info(f"{d.page_content} ({len(d.page_content)})")


if __name__ == "__main__":
    test_word_extractor()
