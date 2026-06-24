import dlt
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/raw")

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
}

COLUMNS = [
    "engine_id", "cycle",
    "setting_1", "setting_2", "setting_3",
] + [f"sensor_{i}" for i in range(1, 22)]

def _load_cmapss_file(path: Path, is_rul: bool = False):
    if is_rul:
        df = pd.read_csv(path, sep=r"\s+", header=None, names=["rul"])
        df["engine_id"] = range(1, len(df) + 1)
        return df
    df = pd.read_csv(path, sep=r"\s+", header=None)
    df = df.iloc[:, :len(COLUMNS)]
    df.columns = COLUMNS
    df["source_file"] = path.stem
    return df


@dlt.resource(name="raw_sensor_readings", write_disposition="replace")
def sensor_readings():
    for name, path in CMAPSS_FILES.items():
        if not path.exists() or "RUL" in name:
            continue
        df = _load_cmapss_file(path)
        yield df.to_dict(orient="records")


@dlt.resource(name="raw_rul_labels", write_disposition="replace")
def rul_labels():
    for name, path in CMAPSS_FILES.items():
        if not path.exists() or "RUL" not in name:
            continue
        df = _load_cmapss_file(path, is_rul=True)
        df["source_file"] = name
        yield df.to_dict(orient="records")


@dlt.source
def cmapss_source():
    return [sensor_readings(), rul_labels()]


def run_pipeline():
    pipeline = dlt.pipeline(
        pipeline_name="cmapss_ingestion",
        destination="duckdb",
        dataset_name="raw",
        dev_mode=False,
    )
    load_info = pipeline.run(cmapss_source())
    print(load_info)
    return load_info


if __name__ == "__main__":
    run_pipeline()