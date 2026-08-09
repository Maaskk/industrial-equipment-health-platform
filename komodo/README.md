# Komodo Configuration

The course administrator owns shared Server `vh3`. The project owns only the existing UI-defined Stack `industrial_equipment_health_platform`.

`resources.toml` was removed because it declared a second Server, Builder, Repo, Build, Procedure, Action, Resource Sync, and User Group that do not exist in the assigned project. Production changes are applied to the existing Stack with `deploy/compose.production.yml`; no duplicate Komodo resources are required.
