from __future__ import annotations

import csv
import json
import sqlite3
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from spass_csv_converter.converter import convert_spass_to_csv


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class ConverterTests(unittest.TestCase):
    def test_converts_json_records(self) -> None:
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "spass_export_data.spass"
            output = tmp_path / "out.csv"
            source.write_text(
                json.dumps({"items": [{"title": "Example", "username": "me", "password": "secret"}]}),
                encoding="utf-8",
            )

            result = convert_spass_to_csv(source, output)

            self.assertEqual(result.row_count, 1)
            rows = read_csv(output)
            self.assertEqual(rows[0]["title"], "Example")
            self.assertEqual(rows[0]["username"], "me")
            self.assertEqual(rows[0]["password"], "secret")

    def test_converts_zipped_json_records(self) -> None:
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "spass_export_data.spass"
            output = tmp_path / "out.csv"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "data/accounts.json",
                    json.dumps([{"url": "https://example.com", "email": "a@b.c"}]),
                )

            result = convert_spass_to_csv(source, output)

            self.assertEqual(result.row_count, 1)
            rows = read_csv(output)
            self.assertEqual(rows[0]["url"], "https://example.com")
            self.assertEqual(rows[0]["source_path"], "data/accounts.json")

    def test_converts_sqlite_records(self) -> None:
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "spass_export_data.spass"
            output = tmp_path / "out.csv"
            connection = sqlite3.connect(source)
            connection.execute("CREATE TABLE logins (title TEXT, username TEXT)")
            connection.execute("INSERT INTO logins VALUES (?, ?)", ("Example", "me"))
            connection.commit()
            connection.close()

            result = convert_spass_to_csv(source, output)

            self.assertEqual(result.row_count, 1)
            rows = read_csv(output)
            self.assertEqual(rows[0]["title"], "Example")
            self.assertEqual(rows[0]["source_table"], "logins")


if __name__ == "__main__":
    unittest.main()
