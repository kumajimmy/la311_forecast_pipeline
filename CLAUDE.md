# la311_forecast_pipeline

## Goal
Build a production-style system that:
- Ingests LA 311 data daily (incremental)
- Transforms into analytics-ready tables
- Produces a NEW rolling 7-day forecast every day
- Tracks accuracy over time and retrains on a schedule
- Serves forecasts via API + dashboard

## Definition of Done (project-level)
- Daily pipeline runs hands-free and writes:
  - actuals table (daily volume by category)
  - forecasts table (next 7 days)
  - metrics table (error trend over time)
- “One command” local verification exists (`make verify`)
- README explains architecture + how to run locally
- Checkpoints exist for easy session restart

## Cadence
- Daily: ingest -> transform -> score next 7 days -> write forecasts + metrics
- Weekly: retrain model and promote only if better (champion/challenger)

## Architecture (high-level)
Source (LA 311 API)
  -> Raw storage (partitioned files)
  -> Warehouse tables (staging + marts)
  -> Forecast pipeline (train/score)
  -> Outputs:
      - fct_311_daily_volume
      - fct_forecast_7d
      - model_metrics
  -> Serving:
      - FastAPI (reads latest forecast + history)
      - Optional Streamlit dashboard

## Repo conventions
- Keep PRs small and verifiable.
- Every change must end with a runnable verification command.
- Prefer config-driven code, avoid hardcoding paths/keys.
- Logging: structured + concise.

## How we use Claude Code
- Start in Plan Mode (agree on plan + acceptance criteria)
- Then implement in auto-accept edits mode
- Always run /verify (or `make verify`)
- End sessions with /checkpoint

## Checkpointing protocol
- `docs/CHECKPOINT.md` = latest status
- `docs/checkpoints/YYYY-MM-DD_HHMM_checkpoint.md` = timestamped history
Each checkpoint includes:
- what changed
- what passed (verify output)
- what’s next (ordered tasks)

## Agent responsibilities
- code-architect: schemas, DAG boundaries, interfaces, acceptance criteria
- data-engineer: ingestion + incremental loads + raw storage
- analytics-engineer: dbt models + tests + docs
- ml-engineer: forecasting + backtests + retraining + model versioning
- devops: docker/airflow wiring + deployment scripts
- build-validator / verify-app: run end-to-end checks; fix wiring regressions

## Verification (must stay green)
- `make verify` is the single source of truth.
- It should validate: lint/format, unit tests, and basic smoke checks.
