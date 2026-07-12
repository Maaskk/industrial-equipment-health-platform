from __future__ import annotations

import argparse
import io
import shutil
import urllib.request
import zipfile
from pathlib import Path


NASA_CMAPSS_URL = (
    "https://phm-datasets.s3.amazonaws.com/NASA/"
    "6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
)

EXPECTED_FILES = [
    *(f"train_FD00{i}.txt" for i in range(1, 5)),
    *(f"test_FD00{i}.txt" for i in range(1, 5)),
    *(f"RUL_FD00{i}.txt" for i in range(1, 5)),
]


def expected_files_present(data_dir: Path) -> bool:
    return all((data_dir / name).exists() for name in EXPECTED_FILES)


def extract_from_archive(archive: zipfile.ZipFile, data_dir: Path) -> bool:
    members_by_name = {Path(member).name: member for member in archive.namelist()}
    if all(name in members_by_name for name in EXPECTED_FILES):
        for name in EXPECTED_FILES:
            source = members_by_name[name]
            target = data_dir / name
            with archive.open(source) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
        return True
    return False


def extract_expected_files(zip_path: Path, data_dir: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        if extract_from_archive(archive, data_dir):
            return

        nested_zip_members = [
            member for member in archive.namelist() if Path(member).name.lower().endswith(".zip")
        ]
        for member in nested_zip_members:
            with archive.open(member) as nested:
                nested_bytes = io.BytesIO(nested.read())
            with zipfile.ZipFile(nested_bytes) as nested_archive:
                if extract_from_archive(nested_archive, data_dir):
                    return

        members_by_name = {Path(member).name: member for member in archive.namelist()}
        missing = [name for name in EXPECTED_FILES if name not in members_by_name]
        raise RuntimeError(f"Archive is missing expected C-MAPSS files: {missing}")


def download_cmapss(data_dir: Path, url: str = NASA_CMAPSS_URL, force: bool = False) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    if expected_files_present(data_dir) and not force:
        print(f"C-MAPSS files already exist in {data_dir}")
        return

    zip_path = data_dir / "cmapss_turbofan.zip"
    print(f"Downloading NASA C-MAPSS archive to {zip_path}")
    urllib.request.urlretrieve(url, zip_path)
    extract_expected_files(zip_path, data_dir)
    print(f"Extracted {len(EXPECTED_FILES)} files to {data_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download NASA C-MAPSS turbofan dataset.")
    parser.add_argument("--data-dir", default="data/raw", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    download_cmapss(args.data_dir, force=args.force)


if __name__ == "__main__":
    main()
