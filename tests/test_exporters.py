import asyncio
import json
from pathlib import Path

import pandas as pd

from tests.factories import villa
from villascout.services.exporters.tabular import CsvExporter, ExcelExporter, JsonExporter


def test_json_exporter_writes_records(tmp_path: Path) -> None:
    output = tmp_path / "villas.json"
    asyncio.run(JsonExporter().export([villa()], output))

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload[0]["name"] == "Casa Verde"
    assert payload[0]["source_listing"]["external_id"] == "place-1"


def test_csv_exporter_writes_flat_records(tmp_path: Path) -> None:
    output = tmp_path / "villas.csv"
    asyncio.run(CsvExporter().export([villa()], output))

    frame = pd.read_csv(output)
    assert frame.loc[0, "name"] == "Casa Verde"
    assert frame.loc[0, "external_id"] == "place-1"


def test_excel_exporter_writes_flat_records(tmp_path: Path) -> None:
    output = tmp_path / "villas.xlsx"
    asyncio.run(ExcelExporter().export([villa()], output))

    frame = pd.read_excel(output)
    assert frame.loc[0, "name"] == "Casa Verde"
    assert frame.loc[0, "external_id"] == "place-1"
