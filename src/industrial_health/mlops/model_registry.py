from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class ModelMetadata:
    name: str = "industrial-equipment-health-model"
    version: str = "1"
    stage: str | None = None

    @classmethod
    def from_environment(cls) -> "ModelMetadata":
        return cls(
            name=getenv("MODEL_NAME", cls.name),
            version=getenv("MODEL_VERSION", cls.version),
            stage=getenv("MODEL_STAGE") or None,
        )


def resolve_model_uri(metadata: ModelMetadata) -> str:
    """Resolve the MLflow model URI used by the serving layer."""

    if metadata.stage:
        return f"models:/{metadata.name}/{metadata.stage}"
    return f"models:/{metadata.name}/{metadata.version}"

