from __future__ import annotations

import argparse
import json
from urllib import request


def read(url: str) -> tuple[int, bytes]:
    with request.urlopen(url, timeout=15) as response:
        return response.status, response.read()


def verify(base_url: str, expected_sha: str | None = None) -> dict[str, object]:
    base = base_url.rstrip("/")
    root_status, root = read(f"{base}/")
    health_status, health_raw = read(f"{base}/health")
    docs_status, _ = read(f"{base}/docs")
    _, payload_raw = read(f"{base}/demo-payload")
    health = json.loads(health_raw)
    payload = json.loads(payload_raw)
    prediction_request = request.Request(
        f"{base}/predict",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(prediction_request, timeout=30) as response:
        prediction_status = response.status
        prediction = json.loads(response.read())

    if root_status != 200 or b"AeroReliability Lab" not in root:
        raise RuntimeError("The university dashboard did not load correctly")
    if health_status != 200 or health.get("model_source") != "mlflow_registry":
        raise RuntimeError("The API did not load the MLflow champion")
    if docs_status != 200 or prediction_status != 200:
        raise RuntimeError("Documentation or prediction verification failed")
    if expected_sha and health.get("release_sha") != expected_sha:
        raise RuntimeError(
            f"Release SHA mismatch: expected {expected_sha}, received {health.get('release_sha')}"
        )
    return {"health": health, "prediction": prediction}


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the deployed university release")
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    result = verify(args.base_url, args.expected_sha)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
