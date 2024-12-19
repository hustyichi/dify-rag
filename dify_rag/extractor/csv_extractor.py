"""Abstract interface for document loader implementations."""

import csv
import os
from typing import Optional

import pandas as pd

from dify_rag.extractor.extractor_base import BaseExtractor
from dify_rag.extractor.utils import get_encoding
from dify_rag.models import constants as global_constants
from dify_rag.models.document import Document


class CSVExtractor(BaseExtractor):
    """Load CSV files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        source_column: Optional[str] = None,
        csv_args: Optional[dict] = None,
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self._encoding = get_encoding(file_path)
        self._file_name = file_name
        if file_name:
            self._file_name = os.path.basename(file_name).split(".")[0]
        self.source_column = source_column
        self.csv_args = csv_args or {}

    def extract(self) -> list[Document]:
        """Load data into document objects."""
        docs = []
        with open(self._file_path, newline="", encoding=self._encoding) as csvfile:
            docs = self._read_from_file(csvfile)
        return docs

    def _read_from_file(self, csvfile) -> list[Document]:
        docs = []
        try:
            # load csv file into pandas dataframe
            df = pd.read_csv(csvfile, on_bad_lines="skip", **self.csv_args)

            # check source column exists
            if self.source_column and self.source_column not in df.columns:
                raise ValueError(
                    f"Source column '{self.source_column}' not found in CSV file."
                )

            # create document objects

            for i, row in df.iterrows():
                content = ";".join(
                    f"{col.strip()}: {str(row[col]).strip()}" for col in df.columns
                )

                source = row[self.source_column] if self.source_column else ""
                metadata = {
                    "source": source,
                    "row": i,
                    "titles": [self._file_name],
                    "content_type": global_constants.ContentType.TABLE,
                }
                doc = Document(page_content=content, metadata=metadata)
                docs.append(doc)
        except csv.Error as e:
            raise e

        return docs
