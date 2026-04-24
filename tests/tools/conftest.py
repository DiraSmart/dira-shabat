"""Shared fixtures: tiny in-memory Excel builder for tests."""
from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import Workbook


@pytest.fixture
def make_xlsx(tmp_path):
    """Return a builder: pass a dict {sheet: rows}, get back an .xlsx Path."""
    def _build(sheets: dict[str, list[list]]) -> BytesIO | str:
        wb = Workbook()
        wb.remove(wb.active)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            for row in rows:
                ws.append(row)
        path = tmp_path / "test.xlsx"
        wb.save(path)
        return path
    return _build
