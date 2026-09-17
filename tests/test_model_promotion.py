from __future__ import annotations

from types import SimpleNamespace

import pytest
from mlflow.exceptions import MlflowException
from mlflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE

from industrial_health.mlops.promotion import decide_and_apply_promotion, evaluate_candidate


class FakeClient:
    def __init__(self, champion=None, champion_metrics=None):
        self.champion = champion
        self.champion_metrics = champion_metrics or {}
        self.alias_updates = []
        self.run_tags = []
        self.version_tags = []

    def get_model_version_by_alias(self, model_name, alias):
        if self.champion is None:
            raise MlflowException(
                f"Registered model alias {alias} not found.",
                error_code=INVALID_PARAMETER_VALUE,
            )
        return self.champion

    def get_run(self, run_id):
        return SimpleNamespace(data=SimpleNamespace(metrics=self.champion_metrics))

    def set_registered_model_alias(self, model_name, alias, version):
        self.alias_updates.append((model_name, alias, version))

    def set_tag(self, run_id, key, value):
        self.run_tags.append((run_id, key, value))

    def set_model_version_tag(self, model_name, version, key, value):
        self.version_tags.append((model_name, version, key, value))


def test_first_candidate_becomes_champion():
    client = FakeClient()

    decision = decide_and_apply_promotion(
        client=client,
        model_name="equipment-model",
        alias="champion",
        candidate_version="1",
        candidate_run_id="run-1",
        candidate_mae=12.0,
        candidate_rmse=17.0,
    )

    assert decision.promoted is True
    assert decision.previous_champion_version is None
    assert client.alias_updates == [("equipment-model", "champion", "1")]


def test_better_candidate_replaces_champion():
    champion = SimpleNamespace(version="4", run_id="run-4")
    client = FakeClient(
        champion=champion,
        champion_metrics={"standard_final_mae": 13.0, "standard_final_rmse": 18.0},
    )

    decision = decide_and_apply_promotion(
        client=client,
        model_name="equipment-model",
        alias="champion",
        candidate_version="5",
        candidate_run_id="run-5",
        candidate_mae=12.5,
        candidate_rmse=17.5,
    )

    assert decision.promoted is True
    assert client.alias_updates[-1] == ("equipment-model", "champion", "5")


def test_worse_candidate_keeps_champion():
    champion = SimpleNamespace(version="4", run_id="run-4")
    client = FakeClient(
        champion=champion,
        champion_metrics={"standard_final_mae": 12.0, "standard_final_rmse": 17.0},
    )

    decision = decide_and_apply_promotion(
        client=client,
        model_name="equipment-model",
        alias="champion",
        candidate_version="5",
        candidate_run_id="run-5",
        candidate_mae=11.5,
        candidate_rmse=17.5,
    )

    assert decision.promoted is False
    assert decision.previous_champion_version == "4"
    assert client.alias_updates == []


def test_incomplete_champion_metrics_block_promotion():
    decision = evaluate_candidate(
        candidate_version="7",
        candidate_mae=10.0,
        candidate_rmse=15.0,
        champion_version="6",
        champion_mae=11.0,
        champion_rmse=None,
    )

    assert decision.promoted is False
    assert "incomplete" in decision.reason.lower()


def test_registry_error_does_not_promote_candidate():
    class FailingClient(FakeClient):
        def get_model_version_by_alias(self, model_name, alias):
            raise MlflowException("registry unavailable")

    with pytest.raises(MlflowException, match="registry unavailable"):
        decide_and_apply_promotion(
            client=FailingClient(),
            model_name="equipment-model",
            alias="champion",
            candidate_version="8",
            candidate_run_id="run-8",
            candidate_mae=9.0,
            candidate_rmse=14.0,
        )
