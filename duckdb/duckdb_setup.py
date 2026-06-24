import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "cmapss_ingestion.duckdb"

def setup_warehouse():
    con = duckdb.connect(str(DB_PATH))

    con.execute("CREATE SCHEMA IF NOT EXISTS staging")
    con.execute("CREATE SCHEMA IF NOT EXISTS marts")

    # ── staging.stg_sensor_readings ──────────────────────────────
    con.execute("DROP TABLE IF EXISTS staging.stg_sensor_readings")
    con.execute("DROP VIEW IF EXISTS staging.stg_sensor_readings")
    con.execute("""
        CREATE TABLE staging.stg_sensor_readings AS
        SELECT engine_id, cycle,
            setting_1, setting_2, setting_3,
            sensor_1, sensor_2, sensor_3, sensor_4, sensor_5,
            sensor_6, sensor_7, sensor_8, sensor_9, sensor_10,
            sensor_11, sensor_12, sensor_13, sensor_14, sensor_15,
            sensor_16, sensor_17, sensor_18, sensor_19, sensor_20,
            sensor_21, source_file
        FROM raw.raw_sensor_readings
        WHERE engine_id IS NOT NULL AND cycle IS NOT NULL
    """)

    # ── staging.stg_rul_labels ───────────────────────────────────
    con.execute("DROP TABLE IF EXISTS staging.stg_rul_labels")
    con.execute("DROP VIEW IF EXISTS staging.stg_rul_labels")
    con.execute("""
        CREATE TABLE staging.stg_rul_labels AS
        SELECT engine_id, rul, source_file
        FROM raw.raw_rul_labels
        WHERE engine_id IS NOT NULL
    """)

    # ── marts.fct_equipment_health_features ──────────────────────
    con.execute("DROP TABLE IF EXISTS marts.fct_equipment_health_features")
    con.execute("DROP VIEW IF EXISTS marts.fct_equipment_health_features")
    con.execute("""
        CREATE TABLE marts.fct_equipment_health_features AS
        WITH base AS (
            SELECT *,
                MAX(cycle) OVER (PARTITION BY engine_id) AS max_cycle
            FROM staging.stg_sensor_readings
        ),
        features AS (
            SELECT
                engine_id,
                cycle,
                setting_1, setting_2, setting_3,
                sensor_1, sensor_2, sensor_3, sensor_4, sensor_5,
                sensor_6, sensor_7, sensor_8, sensor_9, sensor_10,
                sensor_11, sensor_12, sensor_13, sensor_14, sensor_15,
                sensor_16, sensor_17, sensor_18, sensor_19, sensor_20,
                sensor_21,
                source_file,

                -- cycle_norm
                CAST(cycle AS FLOAT) / max_cycle AS cycle_norm,

                -- engine_age_bucket
                CASE
                    WHEN CAST(cycle AS FLOAT) / max_cycle < 0.33 THEN 'young'
                    WHEN CAST(cycle AS FLOAT) / max_cycle < 0.66 THEN 'middle'
                    ELSE 'old'
                END AS engine_age_bucket,

                -- rolling mean 5
                AVG(sensor_1) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_1_rolling_mean_5,
                AVG(sensor_2) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_2_rolling_mean_5,
                AVG(sensor_3) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_3_rolling_mean_5,
                AVG(sensor_4) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_4_rolling_mean_5,
                AVG(sensor_7) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_7_rolling_mean_5,
                AVG(sensor_11) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_11_rolling_mean_5,
                AVG(sensor_12) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_12_rolling_mean_5,
                AVG(sensor_15) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_15_rolling_mean_5,

                -- rolling std 5
                STDDEV(sensor_1) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_1_rolling_std_5,
                STDDEV(sensor_2) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_2_rolling_std_5,
                STDDEV(sensor_3) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_3_rolling_std_5,
                STDDEV(sensor_4) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_4_rolling_std_5,
                STDDEV(sensor_7) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_7_rolling_std_5,
                STDDEV(sensor_11) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_11_rolling_std_5,
                STDDEV(sensor_12) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_12_rolling_std_5,
                STDDEV(sensor_15) OVER (PARTITION BY engine_id ORDER BY cycle ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS sensor_15_rolling_std_5

            FROM base
        )
        SELECT * FROM features
    """)

    # Stats finales
    r1 = con.execute("SELECT COUNT(*) FROM staging.stg_sensor_readings").fetchone()[0]
    r2 = con.execute("SELECT COUNT(*) FROM staging.stg_rul_labels").fetchone()[0]
    r3 = con.execute("SELECT COUNT(*) FROM marts.fct_equipment_health_features").fetchone()[0]

    print(f"DuckDB warehouse ready at {DB_PATH}")
    print(f"staging.stg_sensor_readings      : {r1} lignes")
    print(f"staging.stg_rul_labels           : {r2} lignes")
    print(f"marts.fct_equipment_health_features : {r3} lignes")
    con.close()

if __name__ == "__main__":
    setup_warehouse()