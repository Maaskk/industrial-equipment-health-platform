FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY src ./src
COPY scripts ./scripts

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app/src
EXPOSE 8000

CMD ["python", "scripts/run_api.py"]

