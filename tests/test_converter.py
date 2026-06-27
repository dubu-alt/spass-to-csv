from __future__ import annotations

import csv
import base64
import json
import sqlite3
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from spass_csv_converter.converter import convert_spass_to_csv
from spass_csv_converter.crypto import SPassDecryptor
from spass_csv_converter.models import WarningCode
from spass_csv_converter.spass_parser import SPassParser


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def encrypt_spass_text(plaintext: str, password: str) -> str:
    salt = b"spasstocsv-demo-salt"
    iv = b"demo-iv-12345678"
    key = SPassDecryptor(password)._derive_key(salt)
    padder = padding.PKCS7(SPassDecryptor.BLOCK_SIZE).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(salt + iv + ciphertext).decode("ascii")


DEMO_DECRYPTED = "\n".join(
    [
        "25",
        "true;true;true;true",
        "false",
        "next_table",
        "title;host_url;origin_url;username_value;password_value;credential_memo;otp",
        f"{b64('Example Login')};{b64('https://login.example.com')};{b64('https://login.example.com/sign-in')};{b64('alice@example.com')};{b64('not-a-real-password-1')};{b64('Personal demo entry')};{b64('otpauth://totp/Example:alice@example.com?secret=EXAMPLESECRET&issuer=Example')}",
        f"{b64('Example Admin')};{b64('https://admin.example.com')};{b64('https://admin.example.com/login')};{b64('admin@example.com')};{b64('not-a-real-password-2')};;",
        "next_table",
        "name_on_card;card_number;expiration_month;expiration_year;security_code",
        f"{b64('Demo User')};{b64('4111111111111111')};{b64('12')};{b64('2030')};{b64('123')}",
        "next_table",
        "name;street_address;city;postal_code;country_code",
        f"{b64('Alice Example')};{b64('Example Street 1')};{b64('Zurich')};{b64('8000')};{b64('CH')}",
        "next_table",
        "note_title;note_detail",
        f"{b64('Demo Note')};{b64('This is synthetic fixture data only.')}",
    ]
)


class ConverterTests(unittest.TestCase):
    def test_decrypts_and_exports_chrome_csv(self) -> None:
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "spass_export_data.spass"
            output = tmp_path / "chrome.csv"
            source.write_text(encrypt_spass_text(DEMO_DECRYPTED, "demo-password"), encoding="utf-8")

            result = convert_spass_to_csv(source, output, password="demo-password", format_name="chrome")

            self.assertEqual(result.row_count, 2)
            rows = read_csv(output)
            self.assertEqual(rows[0]["name"], "Example Login")
            self.assertEqual(rows[0]["url"], "https://login.example.com")
            self.assertEqual(rows[0]["username"], "alice@example.com")
            self.assertEqual(rows[0]["password"], "not-a-real-password-1")

    def test_exports_bitwarden_json_with_all_item_types(self) -> None:
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "spass_export_data.spass"
            output = tmp_path / "bitwarden.json"
            source.write_text(encrypt_spass_text(DEMO_DECRYPTED, "demo-password"), encoding="utf-8")

            result = convert_spass_to_csv(source, output, password="demo-password", format_name="bitwarden-json")
            payload = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(result.row_count, 5)
            self.assertEqual([item["type"] for item in payload["items"]], [1, 1, 2, 3, 4])
            self.assertEqual(payload["items"][3]["card"]["number"], "4111111111111111")

    def test_parser_preserves_legacy_raw_fields_with_warnings(self) -> None:
        decrypted = "\n".join(
            [
                "samsung_pass_export",
                "version:1",
                "origin_url;username_value;password_value;credential_memo",
                f"{b64('https://legacy.example.com')};legacy-user;raw-password;{b64('special note')}",
            ]
        )

        parsed = SPassParser.parse_decrypted_data(decrypted)

        self.assertEqual(parsed.passwords[0]["username_value"], "legacy-user")
        self.assertIn(WarningCode.RAW_FIELD_FALLBACK, [warning.code for warning in parsed.warnings])

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
