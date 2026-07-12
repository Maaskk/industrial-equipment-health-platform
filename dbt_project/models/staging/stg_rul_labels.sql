-- Nettoyage des labels RUL bruts ingérés par dlt
-- Equivalent au bloc "staging.stg_rul_labels" de duckdb_setup.py

select
    engine_id,
    rul,
    source_file
from {{ source('raw', 'raw_rul_labels') }}
where engine_id is not null