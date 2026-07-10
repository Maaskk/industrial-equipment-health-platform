# Hamza - Data Quality, Contracts, and Documentation QA

GitHub: `HamzaElhaddaji`

Branch: `feature/HamzaElhaddaji`

## Why this role fits

The public profile has no visible repositories, so this role is important but has a controlled ramp-up. It also touches mandatory project deliverables: data quality, data contract, data lineage, and documentation.

## Mission

Guarantee that the data product is trustworthy and clearly documented.

## Main Deliverables

- Data contract for raw, staging, and feature tables.
- dbt tests for:
  - completeness
  - validity
  - coherence
  - freshness
  - accepted ranges
- Data lineage diagram and explanation.
- Documentation QA checklist.
- Validation evidence for the final report.

## Acceptance Criteria

- Every critical table has documented columns, types, and constraints.
- dbt tests fail when required fields are missing or invalid.
- Data lineage is understandable without reading code.
- Documentation matches the final pipeline behavior.

## First Tasks

1. Draft the data contract from the selected dataset schema.
2. Define required quality tests.
3. Work with Mohamed to place tests in the dbt project.
4. Create lineage documentation.
5. Review README instructions from a fresh-user perspective.
