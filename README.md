# Dify-RAG

**[中文文档](README.zh-CN.md)**

A highly efficient and modular RAG package that can quickly replace the default modules in Dify, significantly improving Dify's RAG performance. It can also serve as a general-purpose foundation package for other open-source RAG services.

# Installation

```bash
pip install dify-rag
```

To use it in a Dify project, add the `dify-rag` dependency in `api/pyproject.toml`, then update the corresponding lock file. There are some differences depending on the Dify version:

- For poetry 1.x, run `poetry lock --no-update` to update the lock file
- For poetry 2.x, run `poetry lock` to update the lock file
- For uv, run `uv lock` to update the lock file

# Usage

The currently implemented modules are plug-and-play and can be directly integrated into the Dify project by replacing the relevant modules. Below is an example using the HTML parser:

In `api/core/rag/extractor/extract_processor.py`, replace the built-in `HtmlExtractor` with the one from Dify-RAG.

Replace the original import:
```python
from core.rag.extractor.html_extractor import HtmlExtractor
```
with:
```python
from dify_rag.extractor.html_extractor import HtmlExtractor
```

Other modules can be replaced in the same way, depending on your needs.

# Supported Document Formats

| Format | Structured Parsing | Table Parsing |
| --- | --- | --- |
| html | Supported | Independent splitting, markdown conversion, row-based splitting |
| md | Supported | Independent splitting, markdown format, row-based splitting |
| docx | Supported | Independent splitting, markdown conversion, row-based splitting |
| pdf | Partial (requires built-in TOC) | Not supported |
| epub | Supported | Independent splitting, markdown conversion, row-based splitting |
| xlsx | Supported | Independent splitting, markdown conversion, row-based splitting |
| csv | Supported | Independent splitting, markdown conversion, row-based splitting |
