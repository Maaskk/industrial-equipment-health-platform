from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import duckdb


RAW_COLUMNS = [
    "cycle",
    "setting_1",
    "setting_2",
    "setting_3",
    *[f"sensor_{index}" for index in range(1, 22)],
]


def build(source: Path, output: Path, model_dir: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Missing source warehouse: {source}")
    if not (model_dir / "model.pkl").exists():
        raise FileNotFoundError(f"Missing serving model: {model_dir / 'model.pkl'}")

    output.mkdir(parents=True, exist_ok=True)
    database = output / "serving.duckdb"
    database.unlink(missing_ok=True)
    connection = duckdb.connect(str(database))
    try:
        connection.execute(f"ATTACH '{source.resolve()}' AS source (READ_ONLY)")
        connection.execute("CREATE SCHEMA marts")
        connection.execute("CREATE SCHEMA staging")
        connection.execute("CREATE SCHEMA raw")
        selected = ", ".join(["engine_id", *RAW_COLUMNS, "split", "subset_id"])
        connection.execute(
            f"""CREATE TABLE marts.fct_equipment_health_features AS
                SELECT {selected}
                FROM source.marts.fct_equipment_health_features
                WHERE split = 'test'"""
        )
        connection.execute(
            """CREATE TABLE staging.stg_rul_labels AS
               SELECT * FROM source.staging.stg_rul_labels"""
        )
        raw_rows = connection.execute(
            "SELECT count(*) FROM source.raw.raw_sensor_readings"
        ).fetchone()[0]
        connection.execute(
            "CREATE TABLE raw.raw_sensor_readings AS SELECT range AS row_id FROM range(?)",
            [raw_rows],
        )
        connection.execute("CHECKPOINT")
    finally:
        connection.close()

    for filename in ("model.pkl", "feature_schema.json", "metrics.json"):
        shutil.copy2(model_dir / filename, output / filename)
    print(f"Vercel serving artifacts created at {output} ({database.stat().st_size:,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compact read-only Vercel artifacts")
    parser.add_argument(
        "--source", type=Path, default=Path("warehouse/cmapss_ingestion.duckdb")
    )
    parser.add_argument("--output", type=Path, default=Path("deploy/vercel"))
    parser.add_argument("--model-dir", type=Path, default=Path("models/latest"))
    args = parser.parse_args()
    build(args.source, args.output, args.model_dir)


if __name__ == "__main__":
    main()
