"""
Tests unitaires — DataOps Infrastructure
Mohamed Kar1 — feature/mohamed-kar1-dataops-infra
"""
import pytest
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "cmapss_ingestion.duckdb"


def get_connection():
    if not DB_PATH.exists():
        pytest.skip(f"DuckDB file not found: {DB_PATH}")
    return duckdb.connect(str(DB_PATH))


# ── 1. DuckDB file exists ─────────────────────────────────────────────────────
def test_duckdb_file_exists():
    """Le fichier DuckDB doit exister après ingestion."""
    assert DB_PATH.exists(), f"cmapss_ingestion.duckdb not found at {DB_PATH}"


# ── 2. Schema raw ─────────────────────────────────────────────────────────────
def test_raw_schema_has_sensor_readings():
    """La table raw.raw_sensor_readings doit exister et contenir des données."""
    con = get_connection()
    count = con.execute("SELECT COUNT(*) FROM raw.raw_sensor_readings").fetchone()[0]
    con.close()
    assert count > 0, "raw.raw_sensor_readings est vide"


def test_raw_schema_has_rul_labels():
    """La table raw.raw_rul_labels doit exister et contenir des données."""
    con = get_connection()
    count = con.execute("SELECT COUNT(*) FROM raw.raw_rul_labels").fetchone()[0]
    con.close()
    assert count > 0, "raw.raw_rul_labels est vide"


# ── 3. Schema staging ─────────────────────────────────────────────────────────
def test_staging_sensor_readings_row_count():
    """staging.stg_sensor_readings doit contenir 265 256 lignes."""
    con = get_connection()
    count = con.execute("SELECT COUNT(*) FROM staging.stg_sensor_readings").fetchone()[0]
    con.close()
    assert count == 265256, f"Expected 265256 rows, got {count}"


def test_staging_sensor_readings_columns():
    """Les colonnes requises par le contrat doivent être présentes."""
    con = get_connection()
    cols = [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='staging' AND table_name='stg_sensor_readings'"
    ).fetchall()]
    con.close()
    required = ["engine_id", "cycle", "setting_1", "setting_2", "setting_3"] + \
               [f"sensor_{i}" for i in range(1, 22)]
    for col in required:
        assert col in cols, f"Colonne manquante: {col}"


def test_staging_no_null_engine_id():
    """Pas de engine_id null dans staging."""
    con = get_connection()
    nulls = con.execute(
        "SELECT COUNT(*) FROM staging.stg_sensor_readings WHERE engine_id IS NULL"
    ).fetchone()[0]
    con.close()
    assert nulls == 0, f"{nulls} lignes avec engine_id NULL"


def test_staging_no_null_cycle():
    """Pas de cycle null dans staging."""
    con = get_connection()
    nulls = con.execute(
        "SELECT COUNT(*) FROM staging.stg_sensor_readings WHERE cycle IS NULL"
    ).fetchone()[0]
    con.close()
    assert nulls == 0, f"{nulls} lignes avec cycle NULL"


# ── 4. Schema marts ───────────────────────────────────────────────────────────
def test_marts_feature_table_exists():
    """marts.fct_equipment_health_features doit exister."""
    con = get_connection()
    count = con.execute(
        "SELECT COUNT(*) FROM marts.fct_equipment_health_features"
    ).fetchone()[0]
    con.close()
    assert count > 0, "marts.fct_equipment_health_features est vide"


def test_marts_feature_engineering_columns():
    """Les colonnes engineered doivent être présentes."""
    con = get_connection()
    cols = [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='marts' AND table_name='fct_equipment_health_features'"
    ).fetchall()]
    con.close()
    required = ["cycle_norm", "engine_age_bucket",
                "sensor_1_rolling_mean_5", "sensor_1_rolling_std_5"]
    for col in required:
        assert col in cols, f"Feature manquante: {col}"


def test_marts_cycle_norm_range():
    """cycle_norm doit être entre 0 et 1."""
    con = get_connection()
    result = con.execute("""
        SELECT MIN(cycle_norm), MAX(cycle_norm)
        FROM marts.fct_equipment_health_features
    """).fetchone()
    con.close()
    assert result[0] >= 0.0, f"cycle_norm min = {result[0]} (doit être >= 0)"
    assert result[1] <= 1.0, f"cycle_norm max = {result[1]} (doit être <= 1)"


def test_marts_engine_age_bucket_values():
    """engine_age_bucket ne doit contenir que young, middle, old."""
    con = get_connection()
    values = {r[0] for r in con.execute(
        "SELECT DISTINCT engine_age_bucket FROM marts.fct_equipment_health_features"
    ).fetchall()}
    con.close()
    assert values.issubset({"young", "middle", "old"}), \
        f"Valeurs inattendues: {values}"