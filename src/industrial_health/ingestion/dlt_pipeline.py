import os
from pathlib import Path

import dlt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("CMAPSS_DATA_DIR", str(PROJECT_ROOT / "data" / "raw")))
DUCKDB_PATH = Path(
    os.getenv("DUCKDB_PATH", str(PROJECT_ROOT / "cmapss_ingestion.duckdb"))
)

CMAPSS_FILES = {
    "train_FD001": DATA_DIR / "train_FD001.txt",
    "train_FD002": DATA_DIR / "train_FD002.txt",
    "train_FD003": DATA_DIR / "train_FD003.txt",
    "train_FD004": DATA_DIR / "train_FD004.txt",
    "test_FD001":  DATA_DIR / "test_FD001.txt",
    "test_FD002":  DATA_DIR / "test_FD002.txt",
    "test_FD003":  DATA_DIR / "test_FD003.txt",
    "test_FD004":  DATA_DIR / "test_FD004.txt",
    "RUL_FD001":   DATA_DIR / "RUL_FD001.txt",
    "RUL_FD002":   DATA_DIR / "RUL_FD002.txt",
    "RUL_FD003":   DATA_DIR / "RUL_FD003.txt",
    "RUL_FD004":   DATA_DIR / "RUL_FD004.txt",
}

COLUMNS = [
    "engine_id", "cycle",
    "setting_1", "setting_2", "setting_3",
] + [f"sensor_{i}" for i in range(1, 22)]


def resolve_dlt_state_dir() -> Path:
    return Path(os.getenv("DLT_DATA_DIR", str(PROJECT_ROOT / ".dlt")))


def prepare_storage(database_path: Path, state_dir: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

def _load_cmapss_file(path: Path, is_rul: bool = False):
    source_name = path.stem
    subset = source_name.replace("RUL_", "")
    if is_rul:
        df = pd.read_csv(path, sep=r"\s+", header=None, names=["rul"])
        df["engine_id"] = [f"test_{subset}_{engine_id}" for engine_id in range(1, len(df) + 1)]
        df["source_file"] = source_name
        return df
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df = df.iloc[:, :len(COLUMNS)]
    df.columns = COLUMNS
    df["engine_id"] = source_name + "_" + df["engine_id"].astype(str)
    df["source_file"] = path.stem
    return df


@dlt.resource(name="raw_sensor_readings", write_disposition="replace")
def sensor_readings():
    for name, path in CMAPSS_FILES.items():
        if not path.exists() or "RUL" in name:
            continue
        df = _load_cmapss_file(path)
        # dlt converts DataFrames to Arrow batches. Avoid materializing hundreds
        # of thousands of Python dictionaries during a clean local rebuild.
        yield df


@dlt.resource(name="raw_rul_labels", write_disposition="replace")
def rul_labels():
    for name, path in CMAPSS_FILES.items():
        if not path.exists() or "RUL" not in name:
            continue
        df = _load_cmapss_file(path, is_rul=True)
        df["source_file"] = name
        yield df


@dlt.source
def cmapss_source():
    return [sensor_readings(), rul_labels()]


def run_pipeline():
    state_dir = resolve_dlt_state_dir()
    prepare_storage(DUCKDB_PATH, state_dir)
    # Keep Arrow batches compatible with dlt's relational table contract.
    dlt.config["normalize.parquet_normalizer.add_dlt_id"] = True
    dlt.config["normalize.parquet_normalizer.add_dlt_load_id"] = True
    pipeline = dlt.pipeline(
        pipeline_name="cmapss_ingestion",
        destination=dlt.destinations.duckdb(credentials=str(DUCKDB_PATH)),
        dataset_name="raw",
        pipelines_dir=str(state_dir),
        dev_mode=False,
    )
    load_info = pipeline.run(cmapss_source())
    print(load_info)
    return load_info


if __name__ == "__main__":
    run_pipeline()
