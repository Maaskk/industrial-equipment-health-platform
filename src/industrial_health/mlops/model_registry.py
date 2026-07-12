from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class ModelMetadata:
    name: str = "industrial-equipment-health-model"
    version: str = "1"
    alias: str | None = None

    @classmethod
    def from_environment(cls) -> "ModelMetadata":
        return cls(
            name=getenv("MODEL_NAME", cls.name),
            version=getenv("MODEL_VERSION", cls.version),
            alias=getenv("MODEL_ALIAS") or None,
        )


def resolve_model_uri(metadata: ModelMetadata) -> str:
    """Resolve the MLflow model URI used by the serving layer."""

    if metadata.alias:
        return f"models:/{metadata.name}@{metadata.alias}"
    return f"models:/{metadata.name}/{metadata.version}"
