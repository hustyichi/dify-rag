# Dify-RAG

高效模块化的 RAG 包，可以快速替换 Dify 中原有的默认模块，大幅提升 Dify 的 RAG 效果。作为通用的基础包，也可以用于其他开源 RAG 服务。

# 安装

```bash
pip install dify-rag
```

为了在 Dify 项目中使用，可以在 `api/pyproject.toml` 中添加 `dify-rag` 依赖，之后调用 `poetry lock --no-update` 更新依赖，即可在 Dify 项目中使用 Dify-RAG 包。

# 使用

目前实现的模块是直接可以插拔放入 Dify 项目中的，只需要在 Dify 项目中替换掉相关模块即可。下面以 html 解析为例：

在 `api/core/rag/extractor/extract_processor.py` 中将原先使用 Dify 内置的 HtmlExtractor 切换为 Dify-RAG 中的 HtmlExtractor 即可。

具体需要将原有的 `from core.rag.extractor.html_extractor import HtmlExtractor` 替换为 `from dify_rag.extractor.html_extractor import HtmlExtractor` 即可

其他模块的替换也是类似的，可以根据自己的需要自行替换增强。

