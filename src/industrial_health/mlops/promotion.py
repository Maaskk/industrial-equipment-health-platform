from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from mlflow.exceptions import MlflowException


@dataclass(frozen=True)
class PromotionDecision:
    candidate_version: str
    previous_champion_version: str | None
    candidate_mae: float
    candidate_rmse: float
    champion_mae: float | None
    champion_rmse: float | None
    promoted: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_candidate(
    *,
    candidate_version: str,
    candidate_mae: float,
    candidate_rmse: float,
    champion_version: str | None,
    champion_mae: float | None,
    champion_rmse: float | None,
) -> PromotionDecision:
    """Compare a candidate with the current champion using both error metrics."""

    if champion_version is None:
        return PromotionDecision(
            candidate_version=candidate_version,
            previous_champion_version=None,
            candidate_mae=candidate_mae,
            candidate_rmse=candidate_rmse,
            champion_mae=None,
            champion_rmse=None,
            promoted=True,
            reason="No champion exists, so the first registered candidate becomes champion.",
        )

    if champion_mae is None or champion_rmse is None:
        return PromotionDecision(
            candidate_version=candidate_version,
            previous_champion_version=champion_version,
            candidate_mae=candidate_mae,
            candidate_rmse=candidate_rmse,
            champion_mae=champion_mae,
            champion_rmse=champion_rmse,
            promoted=False,
            reason="The current champion has incomplete evaluation metrics.",
        )

    promoted = candidate_mae <= champion_mae and candidate_rmse <= champion_rmse
    if promoted:
        reason = "Candidate MAE and RMSE are no worse than the current champion."
    else:
        reason = "Candidate MAE or RMSE is worse than the current champion."
    return PromotionDecision(
        candidate_version=candidate_version,
        previous_champion_version=champion_version,
        candidate_mae=candidate_mae,
        candidate_rmse=candidate_rmse,
        champion_mae=champion_mae,
        champion_rmse=champion_rmse,
        promoted=promoted,
        reason=reason,
    )


def decide_and_apply_promotion(
    *,
    client: Any,
    model_name: str,
    alias: str,
    candidate_version: str,
    candidate_run_id: str,
    candidate_mae: float,
    candidate_rmse: float,
) -> PromotionDecision:
    """Resolve the champion, evaluate the candidate, and update the alias when accepted."""

    try:
        champion = client.get_model_version_by_alias(model_name, alias)
    except MlflowException as exc:
        if exc.error_code != "RESOURCE_DOES_NOT_EXIST":
            raise
        champion = None

    champion_version: str | None = None
    champion_mae: float | None = None
    champion_rmse: float | None = None
    if champion is not None:
        champion_version = str(champion.version)
        champion_run = client.get_run(champion.run_id)
        metrics = champion_run.data.metrics
        champion_mae = metrics.get("standard_final_mae")
        champion_rmse = metrics.get("standard_final_rmse")

    decision = evaluate_candidate(
        candidate_version=candidate_version,
        candidate_mae=candidate_mae,
        candidate_rmse=candidate_rmse,
        champion_version=champion_version,
        champion_mae=champion_mae,
        champion_rmse=champion_rmse,
    )
    if decision.promoted:
        client.set_registered_model_alias(model_name, alias, candidate_version)

    client.set_tag(candidate_run_id, "promotion.alias", alias)
    client.set_tag(candidate_run_id, "promotion.promoted", str(decision.promoted).lower())
    client.set_tag(candidate_run_id, "promotion.reason", decision.reason)
    client.set_model_version_tag(
        model_name,
        candidate_version,
        "promotion.promoted",
        str(decision.promoted).lower(),
    )
    return decision
