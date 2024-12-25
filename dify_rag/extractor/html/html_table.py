#!/usr/bin/python
# -*- coding: utf-8 -*-
# The idea comes from https://github.com/yuanxu-li/html-table-extractor/blob/master/html_table_extractor/extractor.py

import csv
import os

from bs4 import BeautifulSoup, Tag


class HtmlTableExtractor(object):
    def __init__(self, input, id_=None, **kwargs):
        # TODO: should divide this class into two subclasses
        # to deal with string and bs4.Tag separately

        # validate the input
        if not isinstance(input, str) and not isinstance(input, Tag):
            raise Exception("Unrecognized type. Valid input: str, bs4.element.Tag")

        soup = (
            BeautifulSoup(input, "html.parser").find()
            if isinstance(input, str)
            else input
        )

        # locate the target table
        if soup.name == "table":
            self._table = soup
        else:
            self._table = soup.find(id=id_)

        if "transformer" in kwargs:
            self._transformer = kwargs["transformer"]
        else:
            self._transformer = str

        self._output = []

    def parse(self):
        self._output = []
        row_ind = 0
        col_ind = 0
        for row in self._table.find_all("tr"):
            # record the smallest row_span, so that we know how many rows
            # we should skip
            smallest_row_span = 1

            for cell in row.children:
                if cell.name in ("td", "th"):
                    # check multiple rows
                    row_span = int(cell.get("rowspan")) if cell.get("rowspan") else 1

                    # try updating smallest_row_span
                    smallest_row_span = min(smallest_row_span, row_span)

                    # check multiple columns
                    col_span = int(cell.get("colspan")) if cell.get("colspan") else 1

                    # find the right index
                    while True:
                        if self._check_cell_validity(row_ind, col_ind):
                            break
                        col_ind += 1

                    # insert into self._output
                    try:
                        self._insert(
                            row_ind,
                            col_ind,
                            row_span,
                            col_span,
                            self._transformer(cell.get_text()),
                        )
                    except UnicodeEncodeError:
                        raise Exception(
                            "Failed to decode text; you might want to specify kwargs transformer=unicode"
                        )

                    # update col_ind
                    col_ind += col_span

            # update row_ind
            # 进行合并操作
            row_ind += smallest_row_span
            col_ind = 0
        return self

    @staticmethod
    def merge_same_first_column(data: list[list[str]]) -> list[list[str]]:
        """Optimizes complex tables by merging cells with same first column value.

        For rows that have the same value in their first column, merges those rows by:
        - Keeping the first column value from the first row
        - Concatenating values in other columns

        Args:
            data: A 2D list representing the table data

        Returns:
            A 2D list with merged rows where appropriate
        """
        result = []
        i = 0
        while i < len(data):
            current_row = data[i]

            # Check if next row exists and has same first column value
            has_next = i + 1 < len(data)
            should_merge = i == 0 and has_next and data[i + 1][0] == current_row[0] and len(current_row) == len(data[i+1])

            if should_merge:
                next_row = data[i + 1]
                merged_row = []

                # Merge the two rows
                for col in range(len(current_row)):
                    if current_row[col] == next_row[col]:
                        merged_row.append(current_row[col])
                    else:
                        merged_row.append(current_row[col] + " " + next_row[col])

                result.append(merged_row)
                i += 2  # Skip next row since it's been merged
            else:
                result.append(current_row)
                i += 1

        return result

    def format_table(self, table: list[list[str]]) -> list[list[str]]:
        """
        Formatting tables, adding various strategies to improve table presentation
        """
        table = self.merge_same_first_column(table)
        return table

    def return_list(self):
        return self.format_table(self._output)

    def write_to_csv(self, path=".", filename="output.csv"):
        with open(os.path.join(path, filename), "w") as csv_file:
            table_writer = csv.writer(csv_file)
            for row in self._output:
                table_writer.writerow(row)
        return

    def _check_validity(self, i, j, height, width):
        """
        check if a rectangle (i, j, height, width) can be put into self.output
        """
        return all(
            self._check_cell_validity(ii, jj)
            for ii in range(i, i + height)
            for jj in range(j, j + width)
        )

    def _check_cell_validity(self, i, j):
        """
        check if a cell (i, j) can be put into self._output
        """
        if i >= len(self._output):
            return True
        if j >= len(self._output[i]):
            return True
        if self._output[i][j] is None:
            return True
        return False

    def _insert(self, i, j, height, width, val):
        for ii in range(i, i + height):
            for jj in range(j, j + width):
                self._insert_cell(ii, jj, val)

    def _insert_cell(self, i, j, val):
        while i >= len(self._output):
            self._output.append([])
        while j >= len(self._output[i]):
            self._output[i].append(None)

        if self._output[i][j] is None:
            self._output[i][j] = val
