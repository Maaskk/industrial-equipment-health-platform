import sys
import importlib.util
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    print("=== Step 1: Ingestion dlt ===")
    from src.industrial_health.ingestion.dlt_pipeline import run_pipeline
    run_pipeline()

    print("\n=== Step 2: DuckDB setup ===")
    spec = importlib.util.spec_from_file_location(
        "duckdb_setup",
        Path(__file__).parent.parent / "duckdb" / "duckdb_setup.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.setup_warehouse()

    print("\n=== Done. Feature table ready for Mouhcine. ===")