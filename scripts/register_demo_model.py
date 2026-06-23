from pathlib import Path

from industrial_health.mlops.model_loader import FallbackRULModel


def main() -> None:
    """Create a demo model artifact until the ML branch provides the real model.

    This script intentionally avoids requiring MLflow locally. After Mouhcine's
    model exists, Ossama can replace this fallback with MLflow registration.
    """

    import pickle

    model_dir = Path("models/latest")
    model_dir.mkdir(parents=True, exist_ok=True)
    with (model_dir / "model.pkl").open("wb") as file:
        pickle.dump(FallbackRULModel(), file)
    (model_dir / "feature_schema.json").write_text(
        '{\n  "required": ["cycle"],\n  "optional": ["sensor_1", "sensor_2", "sensor_3"]\n}\n',
        encoding="utf-8",
    )
    (model_dir / "metrics.json").write_text(
        '{\n  "model_type": "fallback-demo",\n  "note": "Replace with Mouhcine MLflow model artifact."\n}\n',
        encoding="utf-8",
    )
    print("created demo artifacts in models/latest")


if __name__ == "__main__":
    main()

