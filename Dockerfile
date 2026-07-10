FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/src
ENV CMAPSS_DATA_DIR=/app/data/raw
ENV DUCKDB_PATH=/app/warehouse/cmapss_ingestion.duckdb
ENV DBT_DUCKDB_PATH=/app/warehouse/cmapss_ingestion.duckdb
ENV MLFLOW_TRACKING_URI=sqlite:////app/mlflow/mlflow.db

EXPOSE 8000

CMD ["python", "scripts/run_api.py"]
