"""Run the full pipeline locally without Dagster UI."""
import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt_project"
DUCKDB_PATH = Path(__file__).parent.parent / "cmapss_ingestion.duckdb"
DBT_EXECUTABLE = "dbt"

if __name__ == "__main__":
    print("=== Step 1: Ingestion dlt ===")
    from src.industrial_health.ingestion.dlt_pipeline import run_pipeline
    run_pipeline()

    print("\n=== Step 2: dbt run (staging + marts) ===")
    env = os.environ.copy()
    env["DBT_DUCKDB_PATH"] = str(DUCKDB_PATH)
    subprocess.run(
        [DBT_EXECUTABLE, "run", "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        env=env, check=True,
    )

    print("\n=== Step 3: dbt test ===")
    subprocess.run(
        [DBT_EXECUTABLE, "test", "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        env=env, check=True,
    )

    print("\n=== Done. Feature table ready for Mouhcine. ===")