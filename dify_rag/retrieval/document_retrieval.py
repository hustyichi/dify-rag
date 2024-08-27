# -*- encoding: utf-8 -*-
# File: document_retrieval.py
# Description: None

from dify_rag.models.constants import CUSTOM_SEP
from dify_rag.models.document import Document


def retrieval2reorganize(
    query_docs: list[Document], current_docs_segemts: dict[str : list[Document]]
) -> list[Document]:
    """Reorganize extracted content

    Args:
        query_docs (list[Document]): _description_
        current_docs (list[Document]): _description_

    Returns:
        list[Document]: _description_
    """
    query_docs_map = {}
    query_metadata_map = {}
    title_map = {}
    final_documents_list = []
    for doc in query_docs:
        document_id = doc.metadata.get("document_id")
        title, _ = doc.page_content.split(CUSTOM_SEP)
        query_docs_map[document_id] = query_docs_map.get(document_id, set())
        query_docs_map[document_id].add(title)
        query_metadata_map[f"{document_id}_{title}"] = doc.metadata

    for document_id, docs in current_docs_segemts.items():
        titles = query_docs_map.get(document_id)
        for doc in docs:
            title, content = doc.page_content.split(CUSTOM_SEP)
            if title in titles:
                title_map[f"{document_id}_{title}"] = title_map.get(
                    f"{document_id}_{title}", []
                )
                title_map[f"{document_id}_{title}"].append(content)

    for key, contents in title_map.items():
        doc = Document(
            page_content="".join(contents), metadata=query_metadata_map.get(key, {})
        )
        final_documents_list.append(doc)

    return final_documents_list


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy.sql import text

    engine = create_engine(
        "postgresql+psycopg2://postgres:difyai123456@100.100.30.201:5432/dify"
    )
    db = scoped_session(sessionmaker(bind=engine))

    query_docs_smtm = "select * from document_segments where document_id = '4c1d1ace-ac7b-4b74-a44d-d1e8bfae3b67' order by position"
    current_docs = []
    a = db.execute(text(query_docs_smtm))
    for doc in a.fetchall():
        current_docs.append(
            Document(
                page_content=doc.content,
                metadata={"document_id": "4c1d1ace-ac7b-4b74-a44d-d1e8bfae3b67"},
            )
        )
    query_docs = [current_docs[12], current_docs[-1]]

    print(current_docs)
    print(
        retrieval2reorganize(
            query_docs, {"4c1d1ace-ac7b-4b74-a44d-d1e8bfae3b67": current_docs}
        )
    )
