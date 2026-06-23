# GitHub Remote Setup

The local repository is ready. Remote creation requires a GitHub token or browser session with permission to create public repositories.

## Create the Public Repository

Create this public repository under `Maaskk`:

```text
industrial-equipment-health-platform
```

Recommended description:

```text
Predictive maintenance MLOps and DataOps platform for industrial equipment health.
```

## Push All Branches

After the GitHub repository exists:

```bash
cd /Users/oussamaashad/Documents/Codex/2026-06-23/thi/outputs/industrial-equipment-health-platform
git remote add origin https://github.com/Maaskk/industrial-equipment-health-platform.git
git push -u origin main
git push origin --all
```

## Invite Confirmed Collaborators

Invite these users with write access:

```text
mohamed-kar1
HamzaElhaddaji
Mouhcine005
HajarEnnajdy
```

Pending usernames:

```text
ilyass
akram
```

## Branches

```text
owner/Maaskk-mlops-integration
feature/mohamed-kar1-dataops-infra
feature/HamzaElhaddaji-quality-docs
feature/Mouhcine005-ml-modeling
feature/HajarEnnajdy-api-demo
feature/ilyass-analytics-eda
feature/akram-agile-release
```
