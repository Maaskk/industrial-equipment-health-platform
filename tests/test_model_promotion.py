import json

from scripts.train_model import build_release_manifest, promotion_decision, write_release_manifest


def test_first_registered_model_is_promoted():
    decision = promotion_decision(None, {"mae": 12.5, "rmse": 17.0})

    assert decision["promote"] is True
    assert decision["reason"] == "no_existing_champion"


def test_candidate_must_improve_both_primary_metrics():
    champion = {"mae": 13.0, "rmse": 18.0}

    better = promotion_decision(champion, {"mae": 12.5, "rmse": 17.5})
    mixed = promotion_decision(champion, {"mae": 12.5, "rmse": 18.5})

    assert better["promote"] is True
    assert mixed["promote"] is False
    assert mixed["reason"] == "candidate_did_not_improve_mae_and_rmse"


def test_release_manifest_records_the_deployed_champion(tmp_path):
    manifest = build_release_manifest(
        generated_at="2026-08-09T12:00:00+00:00",
        git_sha="abc123",
        git_tag="professor-demo-v1",
        git_branch="production",
        model_name="industrial-equipment-health-model",
        model_alias="champion",
        model_version="7",
        run_id="run-7",
        subsets=["FD001", "FD002", "FD003", "FD004"],
        final_metrics={"mae": 12.5, "rmse": 17.0, "nasa_score": 101.0},
        promotion={"promote": True, "reason": "candidate_improved_mae_and_rmse"},
    )

    assert manifest["git_sha"] == "abc123"
    assert manifest["git_tag"] == "professor-demo-v1"
    assert manifest["model_version"] == "7"
    assert manifest["model_alias"] == "champion"
    assert manifest["training_subsets"] == ["FD001", "FD002", "FD003", "FD004"]

    json_path, markdown_path = write_release_manifest(tmp_path, manifest)
    assert json.loads(json_path.read_text()) == manifest
    markdown = markdown_path.read_text()
    assert "professor-demo-v1" in markdown
    assert "| Model version | 7 |" in markdown
