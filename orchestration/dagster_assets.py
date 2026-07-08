from dagster import asset, AssetExecutionContext, define_asset_job, ScheduleDefinition, Definitions
from pathlib import Path
import subprocess
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt_project"
DUCKDB_PATH = Path(__file__).parent.parent / "cmapss_ingestion.duckdb"
DBT_EXECUTABLE = "dbt"

def _dbt_env():
    env = os.environ.copy()
    env["DBT_DUCKDB_PATH"] = str(DUCKDB_PATH)
    return env


@asset(group_name="dataops", description="Ingest raw NASA C-MAPSS data into DuckDB via dlt")
def raw_sensor_data(context: AssetExecutionContext):
    from src.industrial_health.ingestion.dlt_pipeline import run_pipeline
    load_info = run_pipeline()
    context.log.info(f"Ingestion done: {load_info}")
    return {"status": "ok", "pipeline": "cmapss_ingestion"}


@asset(group_name="dataops", deps=[raw_sensor_data], description="Run dbt transformations (staging + marts)")
def dbt_transform(context: AssetExecutionContext):
    result = subprocess.run(
        [DBT_EXECUTABLE, "run", "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        env=_dbt_env(),
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception("dbt run failed")
    return {"status": "ok"}


@asset(group_name="dataops", deps=[dbt_transform], description="Run dbt tests on staging and marts models")
def dbt_test(context: AssetExecutionContext):
    result = subprocess.run(
        [DBT_EXECUTABLE, "test", "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        env=_dbt_env(),
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception("dbt test failed")
    return {"status": "ok"}


@asset(group_name="dataops", deps=[dbt_transform], description="Validate feature table schema for Mouhcine's ML pipeline")
def feature_table_validation(context: AssetExecutionContext):
    import duckdb
    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        count = con.execute("SELECT COUNT(*) FROM staging.stg_sensor_readings").fetchone()[0]
        context.log.info(f"Feature table rows: {count}")
        assert count > 0
        return {"status": "valid", "row_count": count}
    finally:
        con.close()


@asset(group_name="dataops", deps=[dbt_transform], description="Feature engineering - fct_equipment_health_features for ML")
def feature_engineering(context: AssetExecutionContext):
    import duckdb
    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        count = con.execute("SELECT COUNT(*) FROM marts.fct_equipment_health_features").fetchone()[0]
        context.log.info(f"fct_equipment_health_features rows: {count}")
        assert count > 0
        return {"status": "ok", "row_count": count}
    finally:
        con.close()


ingestion_job = define_asset_job(
    name="full_ingestion_job",
    selection=["raw_sensor_data", "dbt_transform", "dbt_test", "feature_table_validation", "feature_engineering"]
)

daily_schedule = ScheduleDefinition(
    job=ingestion_job,
    cron_schedule="0 6 * * *",
)

defs = Definitions(
    assets=[raw_sensor_data, dbt_transform, dbt_test, feature_table_validation, feature_engineering],
    jobs=[ingestion_job],
    schedules=[daily_schedule],
)