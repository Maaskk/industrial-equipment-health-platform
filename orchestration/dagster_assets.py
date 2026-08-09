from dagster import (
    AssetExecutionContext,
    DefaultScheduleStatus,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
    in_process_executor,
)
from pathlib import Path
import subprocess
import sys
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

DBT_PROJECT_DIR = Path(__file__).parent.parent / "dbt_project"
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", Path(__file__).parent.parent / "cmapss_ingestion.duckdb"))


def _dbt_command(command: str) -> list[str]:
    configured = os.getenv("DBT_EXECUTABLE")
    if configured:
        return [configured, command]
    executable = Path(sys.executable).with_name("dbt")
    if executable.exists():
        return [str(executable), command]
    return [sys.executable, "-m", "dbt.cli.main", command]

def _dbt_env():
    env = os.environ.copy()
    env["DBT_DUCKDB_PATH"] = str(DUCKDB_PATH)
    return env


@asset(group_name="dataops", description="Ingest raw NASA C-MAPSS data into DuckDB via dlt")
def raw_sensor_data(context: AssetExecutionContext):
    from industrial_health.ingestion.dlt_pipeline import run_pipeline
    load_info = run_pipeline()
    context.log.info(f"Ingestion done: {load_info}")
    return {"status": "ok", "pipeline": "cmapss_ingestion"}


@asset(group_name="dataops", deps=[raw_sensor_data], description="Run dbt transformations (staging + marts)")
def dbt_transform(context: AssetExecutionContext):
    result = subprocess.run(
        [*_dbt_command("run"), "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
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
        [*_dbt_command("test"), "--project-dir", str(DBT_PROJECT_DIR), "--profiles-dir", str(DBT_PROJECT_DIR)],
        capture_output=True,
        text=True,
        env=_dbt_env(),
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise Exception("dbt test failed")
    return {"status": "ok"}


@asset(group_name="dataops", deps=[dbt_test], description="Validate the staged row contract after dbt tests")
def feature_table_validation(context: AssetExecutionContext):
    import duckdb
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        count = con.execute("SELECT COUNT(*) FROM staging.stg_sensor_readings").fetchone()[0]
        context.log.info(f"Feature table rows: {count}")
        assert count > 0
        return {"status": "valid", "row_count": count}
    finally:
        con.close()


@asset(group_name="dataops", deps=[feature_table_validation], description="Validate the final dbt feature mart for ML")
def feature_engineering(context: AssetExecutionContext):
    import duckdb
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        count = con.execute("SELECT COUNT(*) FROM marts.fct_equipment_health_features").fetchone()[0]
        context.log.info(f"fct_equipment_health_features rows: {count}")
        assert count > 0
        return {"status": "ok", "row_count": count}
    finally:
        con.close()


@asset(
    group_name="mlops",
    deps=[feature_engineering],
    description="Train, evaluate, register, and alias the final C-MAPSS model in MLflow",
)
def model_training(context: AssetExecutionContext):
    command = [sys.executable, "scripts/execute_training_notebook.py", "--duckdb-path", str(DUCKDB_PATH)]
    result = subprocess.run(
        command,
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise RuntimeError("Model training or MLflow registration failed")
    metrics_path = Path(__file__).parent.parent / "reports/model_metrics/final_evaluation.json"
    if not metrics_path.exists():
        raise RuntimeError("Training completed without the required evaluation artifact")
    return {"status": "registered", "metrics_path": str(metrics_path)}


@asset(group_name="mlops", deps=[model_training], description="Generate the local prediction drift report")
def drift_report(context: AssetExecutionContext):
    result = subprocess.run(
        [sys.executable, "scripts/generate_drift_report.py"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        context.log.error(result.stderr)
        raise RuntimeError("Drift report generation failed")
    return {"status": "ok", "report": "reports/monitoring/drift_report.json"}


final_mlops_job = define_asset_job(
    name="final_mlops_job",
    executor_def=in_process_executor,
    selection=[
        "raw_sensor_data",
        "dbt_transform",
        "dbt_test",
        "feature_table_validation",
        "feature_engineering",
        "model_training",
        "drift_report",
    ],
)

daily_schedule = ScheduleDefinition(
    job=final_mlops_job,
    cron_schedule="0 6 * * *",
    execution_timezone="Africa/Casablanca",
    default_status=DefaultScheduleStatus.RUNNING,
)

defs = Definitions(
    assets=[
        raw_sensor_data,
        dbt_transform,
        dbt_test,
        feature_table_validation,
        feature_engineering,
        model_training,
        drift_report,
    ],
    jobs=[final_mlops_job],
    schedules=[daily_schedule],
)
