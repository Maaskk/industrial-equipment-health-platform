import hashlib
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from scripts import download_data
from industrial_health.ingestion import dlt_pipeline


class ReproducibleDataOpsTests(unittest.TestCase):
    def test_nasa_archive_checksum_matches_the_verified_source(self):
        self.assertEqual(
            download_data.NASA_CMAPSS_SHA256,
            "c9c5dec12a945a82e8bb4446589d7fb3cc057b5e5d81fa1a12e25ee9912ad3b2",
        )

    def test_checksum_validation_rejects_modified_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "archive.zip"
            archive.write_bytes(b"modified")

            with self.assertRaisesRegex(RuntimeError, "checksum"):
                download_data.verify_sha256(archive, "0" * 64)

    def test_checksum_validation_accepts_expected_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "archive.zip"
            archive.write_bytes(b"verified")
            expected = hashlib.sha256(b"verified").hexdigest()

            download_data.verify_sha256(archive, expected)

    def test_download_uses_verified_ca_bundle(self):
        response = BytesIO(b"archive")
        response.__enter__ = lambda value: value
        response.__exit__ = lambda *args: None
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "archive.zip"
            with patch("scripts.download_data.urllib.request.urlopen", return_value=response) as open_url:
                download_data.download_file("https://example.test/archive.zip", target)

        self.assertTrue(open_url.call_args.kwargs["context"].verify_mode)

    def test_default_dlt_state_is_inside_the_repository(self):
        with patch.dict(os.environ, {}, clear=True):
            state_dir = dlt_pipeline.resolve_dlt_state_dir()

        self.assertEqual(state_dir, dlt_pipeline.PROJECT_ROOT / ".dlt")

    def test_dlt_state_environment_override_is_respected(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"DLT_DATA_DIR": directory}):
                state_dir = dlt_pipeline.resolve_dlt_state_dir()

        self.assertEqual(state_dir, Path(directory))

    def test_storage_directories_are_created_explicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "warehouse" / "pipeline.duckdb"
            state = root / "state"

            dlt_pipeline.prepare_storage(database, state)

            self.assertTrue(database.parent.is_dir())
            self.assertTrue(state.is_dir())


if __name__ == "__main__":
    unittest.main()
