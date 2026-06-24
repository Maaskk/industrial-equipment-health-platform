from dagster import asset, AssetExecutionContext, define_asset_job, ScheduleDefinition, Definitions
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


@asset(group_name="dataops", description="Ingest raw NASA C-MAPSS data into DuckDB via dlt")
def raw_sensor_data(context: AssetExecutionContext):
    from src.industrial_health.ingestion.dlt_pipeline import run_pipeline
    load_info = run_pipeline()
    context.log.info(f"Ingestion done: {load_info}")
    return {"status": "ok", "pipeline": "cmapss_ingestion"}


@asset(group_name="dataops", deps=[raw_sensor_data], description="Setup DuckDB schemas and staging tables")
def duckdb_warehouse(context: AssetExecutionContext):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "duckdb_setup",
        Path(__file__).parent.parent / "duckdb" / "duckdb_setup.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.setup_warehouse()
    context.log.info("DuckDB warehouse configured")
    return {"status": "ok"}


@asset(group_name="dataops", deps=[duckdb_warehouse], description="Validate feature table schema for Mouhcine's ML pipeline")
def feature_table_validation(context: AssetExecutionContext):
    import duckdb
    db_path = str(Path(__file__).parent.parent / "cmapss_ingestion.duckdb")
    con = duckdb.connect(db_path)
    try:
        count = con.execute("SELECT COUNT(*) FROM staging.stg_sensor_readings").fetchone()[0]
        context.log.info(f"Feature table rows: {count}")
        assert count > 0
        return {"status": "valid", "row_count": count}
    finally:
        con.close()


@asset(group_name="dataops", deps=[duckdb_warehouse], description="Feature engineering - fct_equipment_health_features for ML")
def feature_engineering(context: AssetExecutionContext):
    import duckdb
    db_path = str(Path(__file__).parent.parent / "cmapss_ingestion.duckdb")
    con = duckdb.connect(db_path)
    try:
        count = con.execute("SELECT COUNT(*) FROM marts.fct_equipment_health_features").fetchone()[0]
        context.log.info(f"fct_equipment_health_features rows: {count}")
        assert count > 0
        return {"status": "ok", "row_count": count}
    finally:
        con.close()


ingestion_job = define_asset_job(
    name="full_ingestion_job",
    selection=["raw_sensor_data", "duckdb_warehouse", "feature_table_validation", "feature_engineering"]
)

daily_schedule = ScheduleDefinition(
    job=ingestion_job,
    cron_schedule="0 6 * * *",
)

defs = Definitions(
    assets=[raw_sensor_data, duckdb_warehouse, feature_table_validation, feature_engineering],
    jobs=[ingestion_job],
    schedules=[daily_schedule],
)