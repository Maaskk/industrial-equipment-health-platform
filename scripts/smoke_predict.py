import json
from urllib import request

from industrial_health.mlops.smoke import build_sample_payload, validate_prediction_response


def main() -> None:
    payload = json.dumps(build_sample_payload()).encode("utf-8")
    api_request = request.Request(
        "http://localhost:8000/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(api_request, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    validate_prediction_response(body)
    print(json.dumps(body, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

