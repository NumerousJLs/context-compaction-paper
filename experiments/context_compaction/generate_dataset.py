from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path

from task_utils import dump_json


RECENT_TURNS = [
    {"speaker": "user", "text": "We compacted the earlier session because the chat was getting long."},
    {"speaker": "assistant", "text": "I can resume once I recover the active task state from the earlier context."},
    {"speaker": "user", "text": "Please recover the current state exactly before taking the next step."},
]


LATEST_CONSTRAINT_SPECS = [
    {
        "task_id": "lc01",
        "scenario": "Flask user search endpoint",
        "goal": "Finish the Flask user search endpoint so filtered queries work again.",
        "goal_distractors": [
            "Rewrite the React search modal for the user dashboard.",
            "Add a new Elasticsearch cluster for user search."
        ],
        "file": "api/routes/user_search.py",
        "stale_file": "api/routes/users.py",
        "extra_file": "tests/api/test_user_search.py",
        "file_hint": "the user search route module",
        "constraint": "Use Postgres ILIKE filters and do not reintroduce SQLite-specific query code.",
        "constraint_hint": "the newer Postgres-only query rule",
        "stale_constraint": "Keep the old SQLite LIKE query because production still mirrors local dev.",
        "extra_constraint": "Move the search to Elasticsearch before fixing the endpoint.",
        "detail": "Remember that the failing case is `GET /users/search?q=jo` returning an empty list.",
        "detail_hint": "the empty-result search regression on `q=jo`",
        "stale_detail": "The old failure was a timeout on `GET /users?page=2`.",
        "extra_detail": "The main issue is a CSS overflow in the search drawer.",
        "next_step": "Edit `api/routes/user_search.py` to switch the query builder to Postgres ILIKE and rerun `pytest tests/api/test_user_search.py -q`.",
        "next_step_distractors": [
            "Edit `api/routes/users.py` and keep the SQLite query path in place.",
            "Skip the backend and only change the search modal placeholder text."
        ],
        "completed": "The request parser and pagination fix are already done.",
        "open_issue": "The search handler is still using the outdated SQLite query path.",
        "failure_mode": "late database constraint correction",
    },
    {
        "task_id": "lc02",
        "scenario": "CSV ingestion worker",
        "goal": "Restore the nightly CSV ingestion worker without changing the upstream file format.",
        "goal_distractors": [
            "Migrate the ingestion pipeline to Avro first.",
            "Add a brand new upload UI for CSV imports."
        ],
        "file": "workers/csv_ingest.py",
        "stale_file": "workers/import_runner.py",
        "extra_file": "scripts/replay_csv_job.sh",
        "file_hint": "the CSV ingest worker",
        "constraint": "Do not add pandas; keep the fix in the standard library parser.",
        "constraint_hint": "the no-new-dependency parsing rule",
        "stale_constraint": "Add pandas and rewrite the parser around DataFrames.",
        "extra_constraint": "Switch the job to read Parquet instead of CSV.",
        "detail": "Preserve the exact delimiter override `delimiter='|'` for partner feeds.",
        "detail_hint": "the pipe-delimiter override for partner feeds",
        "stale_detail": "The only important flag is `delimiter=','` for local tests.",
        "extra_detail": "The main problem is an S3 bucket policy change.",
        "next_step": "Update `workers/csv_ingest.py` to keep the standard library parser, preserve `delimiter='|'`, and rerun `python scripts/replay_csv_job.sh --sample partner_feed`.",
        "next_step_distractors": [
            "Rewrite the importer with pandas in `workers/import_runner.py`.",
            "Ignore the parser and work on the upload UI instead."
        ],
        "completed": "The retry wrapper and checkpoint writes already work.",
        "open_issue": "The parser fix still points at the wrong dependency choice.",
        "failure_mode": "late dependency restriction",
    },
    {
        "task_id": "lc03",
        "scenario": "Webhook signature middleware",
        "goal": "Fix webhook signature verification so billing callbacks stop failing in staging.",
        "goal_distractors": [
            "Create a new billing dashboard tab for webhook history.",
            "Rotate all production secrets and redeploy the entire stack."
        ],
        "file": "middleware/webhook_signature.py",
        "stale_file": "routes/webhooks.py",
        "extra_file": "tests/test_webhook_signature.py",
        "file_hint": "the webhook signature middleware",
        "constraint": "Use the raw request body bytes; do not verify against the parsed JSON string.",
        "constraint_hint": "the raw-bytes verification rule",
        "stale_constraint": "Keep hashing the parsed JSON string because it is easier to debug.",
        "extra_constraint": "Move verification entirely into the frontend dev proxy.",
        "detail": "The exact header to keep is `X-Signature-Timestamp`.",
        "detail_hint": "the timestamp signature header",
        "stale_detail": "The only header that matters is `X-Request-Id`.",
        "extra_detail": "The main bug is a CSS issue in the staging admin page.",
        "next_step": "Edit `middleware/webhook_signature.py` to verify the raw body bytes and preserve `X-Signature-Timestamp`, then rerun `pytest tests/test_webhook_signature.py -q`.",
        "next_step_distractors": [
            "Edit `routes/webhooks.py` and keep verifying the parsed JSON string.",
            "Skip verification and work on the billing dashboard tab."
        ],
        "completed": "Route registration and secret loading already work.",
        "open_issue": "The signature check still uses the wrong payload representation.",
        "failure_mode": "late verification-method correction",
    },
    {
        "task_id": "lc04",
        "scenario": "Static site build script",
        "goal": "Repair the static site build script so preview deploys succeed again.",
        "goal_distractors": [
            "Replace the static site generator with Next.js.",
            "Create a new design system for the marketing site."
        ],
        "file": "scripts/build_preview.sh",
        "stale_file": "scripts/deploy_preview.sh",
        "extra_file": "docs/preview_build.md",
        "file_hint": "the preview build script",
        "constraint": "Keep the build POSIX-shell compatible; do not switch to bash arrays.",
        "constraint_hint": "the POSIX shell compatibility rule",
        "stale_constraint": "Rewrite the script with bash-only arrays and associative maps.",
        "extra_constraint": "Move the preview build into a GitHub Action before fixing the script.",
        "detail": "The exact environment variable still required is `PREVIEW_BASE_URL`.",
        "detail_hint": "the preview base URL environment variable",
        "stale_detail": "Only `SITE_THEME` matters for this failure.",
        "extra_detail": "The real issue is a missing Figma asset export.",
        "next_step": "Update `scripts/build_preview.sh` to stay POSIX compatible, keep `PREVIEW_BASE_URL`, and rerun `sh scripts/build_preview.sh --dry-run`.",
        "next_step_distractors": [
            "Rewrite `scripts/deploy_preview.sh` with bash arrays.",
            "Skip the script and redesign the marketing site."
        ],
        "completed": "Asset copying and preview folder cleanup already work.",
        "open_issue": "The script still assumes bash-specific syntax.",
        "failure_mode": "late shell-compatibility correction",
    },
    {
        "task_id": "lc05",
        "scenario": "Metrics exporter",
        "goal": "Fix the Prometheus metrics exporter so queue metrics appear again.",
        "goal_distractors": [
            "Rewrite the observability stack around OpenTelemetry collectors.",
            "Add a new dashboard theme for Grafana."
        ],
        "file": "observability/queue_metrics.py",
        "stale_file": "observability/exporter.py",
        "extra_file": "tests/test_queue_metrics.py",
        "file_hint": "the queue metrics module",
        "constraint": "Keep the metric names stable; do not rename `queue_depth_total`.",
        "constraint_hint": "the no-metric-rename rule",
        "stale_constraint": "Rename everything to `job_queue_depth_total` while fixing the bug.",
        "extra_constraint": "Drop Prometheus and emit logs only.",
        "detail": "The missing metric is exactly `queue_depth_total`.",
        "detail_hint": "the missing `queue_depth_total` metric",
        "stale_detail": "The only missing metric is `request_latency_ms`.",
        "extra_detail": "The actual issue is a Grafana panel color mismatch.",
        "next_step": "Edit `observability/queue_metrics.py` to restore `queue_depth_total` without renaming it, then rerun `pytest tests/test_queue_metrics.py -q`.",
        "next_step_distractors": [
            "Edit `observability/exporter.py` and rename the metric family.",
            "Ignore the exporter and retheme the dashboard."
        ],
        "completed": "The registry wiring and scrape endpoint already work.",
        "open_issue": "The queue metric code still points at the wrong name.",
        "failure_mode": "late metric-name preservation rule",
    },
    {
        "task_id": "lc06",
        "scenario": "Authentication callback handler",
        "goal": "Repair the OAuth callback handler so the login redirect flow finishes correctly.",
        "goal_distractors": [
            "Build a new login screen animation for the app.",
            "Replace OAuth with SAML before fixing the callback."
        ],
        "file": "auth/callback_handler.py",
        "stale_file": "auth/session_store.py",
        "extra_file": "tests/test_callback_handler.py",
        "file_hint": "the OAuth callback handler",
        "constraint": "Validate the `state` parameter before exchanging the auth code.",
        "constraint_hint": "the validate-state-before-exchange rule",
        "stale_constraint": "Exchange the auth code first and validate `state` later.",
        "extra_constraint": "Skip state validation in staging for easier testing.",
        "detail": "The exact redirect path must remain `/auth/callback`.",
        "detail_hint": "the `/auth/callback` redirect path",
        "stale_detail": "The only path that matters is `/auth/login`.",
        "extra_detail": "The problem is a spacing issue in the login button text.",
        "next_step": "Edit `auth/callback_handler.py` to validate `state` before code exchange and keep `/auth/callback`, then rerun `pytest tests/test_callback_handler.py -q`.",
        "next_step_distractors": [
            "Edit `auth/session_store.py` and keep validating `state` later.",
            "Skip the backend and animate the login screen."
        ],
        "completed": "Session persistence and redirect mapping already work.",
        "open_issue": "The callback still applies the wrong ordering for state validation.",
        "failure_mode": "late ordering correction",
    },
    {
        "task_id": "lc07",
        "scenario": "Email templating command",
        "goal": "Stabilize the email preview command so transactional templates render correctly.",
        "goal_distractors": [
            "Migrate the whole mail system to a third-party vendor.",
            "Create a new visual email builder."
        ],
        "file": "cli/email_preview.py",
        "stale_file": "mail/render.py",
        "extra_file": "tests/test_email_preview.py",
        "file_hint": "the email preview CLI",
        "constraint": "Keep Jinja autoescaping enabled; do not disable it for convenience.",
        "constraint_hint": "the autoescaping must stay on rule",
        "stale_constraint": "Turn off Jinja autoescaping so previews match the old snapshots.",
        "extra_constraint": "Replace Jinja with MJML before fixing the command.",
        "detail": "The preview command still needs `--template welcome_email`.",
        "detail_hint": "the `--template welcome_email` preview flag",
        "stale_detail": "The only important flag is `--template password_reset`.",
        "extra_detail": "The main issue is a font mismatch in the preview browser.",
        "next_step": "Update `cli/email_preview.py` to keep autoescaping enabled and preserve `--template welcome_email`, then rerun `pytest tests/test_email_preview.py -q`.",
        "next_step_distractors": [
            "Edit `mail/render.py` and disable autoescaping.",
            "Ignore the CLI and build a visual email editor."
        ],
        "completed": "The fixture loader and snapshot refresh script already work.",
        "open_issue": "The preview command still takes the unsafe rendering shortcut.",
        "failure_mode": "late security constraint correction",
    },
    {
        "task_id": "lc08",
        "scenario": "Task scheduler timezone fix",
        "goal": "Fix the task scheduler so reminders fire in the correct local timezone.",
        "goal_distractors": [
            "Add a new calendar UI for reminder templates.",
            "Replace the scheduler with a managed third-party service."
        ],
        "file": "scheduler/reminder_jobs.py",
        "stale_file": "scheduler/job_runner.py",
        "extra_file": "tests/test_reminder_jobs.py",
        "file_hint": "the reminder job scheduler",
        "constraint": "Use the user's stored IANA timezone; do not fall back to the server timezone.",
        "constraint_hint": "the use-stored-IANA-timezone rule",
        "stale_constraint": "Use the server timezone because it matches staging.",
        "extra_constraint": "Convert every reminder to UTC text before scheduling it.",
        "detail": "The exact timezone field is `user.timezone_name`.",
        "detail_hint": "the `user.timezone_name` field",
        "stale_detail": "The only important field is `user.locale`.",
        "extra_detail": "The root problem is a CSS issue in the reminders settings page.",
        "next_step": "Edit `scheduler/reminder_jobs.py` to read `user.timezone_name` and stop using the server timezone, then rerun `pytest tests/test_reminder_jobs.py -q`.",
        "next_step_distractors": [
            "Edit `scheduler/job_runner.py` and keep using the server timezone.",
            "Ignore scheduling and build a new calendar UI."
        ],
        "completed": "The reminder selection query already works.",
        "open_issue": "The scheduler still picks the wrong timezone source.",
        "failure_mode": "late timezone-source correction",
    },
]


BRITTLE_DETAIL_SPECS = [
    {
        "task_id": "bd01",
        "scenario": "Docker compose startup command",
        "goal": "Recover the local compose startup flow for the API and worker stack.",
        "goal_distractors": [
            "Replace Docker Compose with Kubernetes manifests.",
            "Design a new local setup walkthrough page."
        ],
        "file": "docker/docker-compose.dev.yml",
        "stale_file": "docker/Dockerfile.api",
        "extra_file": "scripts/dev_up.sh",
        "file_hint": "the dev compose configuration",
        "constraint": "Keep the existing service names; do not rename containers while debugging.",
        "constraint_hint": "the keep-service-names rule",
        "stale_constraint": "Rename the API and worker services to make the stack clearer.",
        "extra_constraint": "Move the whole stack to Nomad before debugging.",
        "detail": "The exact startup command is `docker compose -f docker/docker-compose.dev.yml up api worker`.",
        "detail_hint": "the compose command that starts only api and worker",
        "stale_detail": "The old command was `docker compose up db cache`.",
        "extra_detail": "The issue is just a broken screenshot in the docs.",
        "next_step": "Use `docker compose -f docker/docker-compose.dev.yml up api worker` and keep the service names unchanged while fixing `docker/docker-compose.dev.yml`.",
        "next_step_distractors": [
            "Rename the services and only start db plus cache.",
            "Skip the compose file and edit the docs screenshot."
        ],
        "completed": "The images build successfully and env files load.",
        "open_issue": "The dev startup instructions still point at the wrong command.",
        "failure_mode": "lost exact startup command",
    },
    {
        "task_id": "bd02",
        "scenario": "Regex validator",
        "goal": "Fix the coupon code validator without changing the accepted format.",
        "goal_distractors": [
            "Rebrand coupon codes with a brand-new format.",
            "Build a coupon admin UI first."
        ],
        "file": "validators/coupon_code.py",
        "stale_file": "routes/coupons.py",
        "extra_file": "tests/test_coupon_code.py",
        "file_hint": "the coupon validator module",
        "constraint": "Do not widen the accepted pattern; the existing format stays strict.",
        "constraint_hint": "the keep-the-format-strict rule",
        "stale_constraint": "Accept any alphanumeric string to reduce user friction.",
        "extra_constraint": "Move validation into the browser first.",
        "detail": "The exact regex is `^[A-Z]{3}-\\d{4}$`.",
        "detail_hint": "the three-letters dash four-digits regex",
        "stale_detail": "The old regex was `^[A-Z0-9]{4,8}$`.",
        "extra_detail": "The issue is a color mismatch in the coupon modal.",
        "next_step": "Edit `validators/coupon_code.py` to preserve `^[A-Z]{3}-\\d{4}$` and rerun `pytest tests/test_coupon_code.py -q`.",
        "next_step_distractors": [
            "Edit `routes/coupons.py` and widen the format to any alphanumeric string.",
            "Skip validation and restyle the coupon modal."
        ],
        "completed": "The parser and normalization step already work.",
        "open_issue": "The exact regex was dropped during refactoring.",
        "failure_mode": "lost exact regex detail",
    },
    {
        "task_id": "bd03",
        "scenario": "Env loader bug",
        "goal": "Repair the environment loader so staging secrets resolve again.",
        "goal_distractors": [
            "Move secrets management to a new vendor before fixing the loader.",
            "Create a security dashboard for missing env vars."
        ],
        "file": "config/env_loader.py",
        "stale_file": "config/settings.py",
        "extra_file": "tests/test_env_loader.py",
        "file_hint": "the environment loader",
        "constraint": "Keep the existing secret name mapping; do not rename the env vars.",
        "constraint_hint": "the preserve-existing-env-names rule",
        "stale_constraint": "Rename the env vars to a cleaner prefix while fixing the bug.",
        "extra_constraint": "Hardcode the secret locally to unblock staging.",
        "detail": "The exact variable is `PAYMENTS_SIGNING_SECRET`.",
        "detail_hint": "the payments signing secret variable",
        "stale_detail": "The old variable was `PAYMENT_SECRET`.",
        "extra_detail": "The main issue is a spacing bug in the settings panel.",
        "next_step": "Edit `config/env_loader.py` to preserve `PAYMENTS_SIGNING_SECRET` and rerun `pytest tests/test_env_loader.py -q`.",
        "next_step_distractors": [
            "Edit `config/settings.py` and rename the variable to `PAYMENT_SECRET`.",
            "Ignore the loader and build a dashboard for missing env vars."
        ],
        "completed": "The `.env` file is found and fallback loading works.",
        "open_issue": "The loader still points at the wrong secret name.",
        "failure_mode": "lost exact env var",
    },
    {
        "task_id": "bd04",
        "scenario": "SQL migration guard",
        "goal": "Fix the migration guard so the billing schema patch can run safely.",
        "goal_distractors": [
            "Rewrite the whole billing schema from scratch.",
            "Make a visual migration status page first."
        ],
        "file": "db/migrations/guard.py",
        "stale_file": "db/migrations/runner.py",
        "extra_file": "tests/test_migration_guard.py",
        "file_hint": "the migration guard",
        "constraint": "Do not drop existing rows; keep the migration additive.",
        "constraint_hint": "the additive-only migration rule",
        "stale_constraint": "Delete old rows to make the schema patch simpler.",
        "extra_constraint": "Skip the guard and patch the database manually.",
        "detail": "The exact migration identifier is `2026_04_add_billing_status_index`.",
        "detail_hint": "the billing status index migration id",
        "stale_detail": "The old migration id was `2026_03_drop_invoice_flags`.",
        "extra_detail": "The issue is just a stale screenshot in the runbook.",
        "next_step": "Edit `db/migrations/guard.py` to preserve the additive guard for `2026_04_add_billing_status_index`, then rerun `pytest tests/test_migration_guard.py -q`.",
        "next_step_distractors": [
            "Edit `db/migrations/runner.py` and delete old rows for `2026_03_drop_invoice_flags`.",
            "Ignore the guard and update the runbook screenshot."
        ],
        "completed": "The schema diff and dry-run path already work.",
        "open_issue": "The guard lost the exact migration identifier during the refactor.",
        "failure_mode": "lost exact migration id",
    },
    {
        "task_id": "bd05",
        "scenario": "Search CLI flag regression",
        "goal": "Restore the search reindex CLI so targeted reindexing works again.",
        "goal_distractors": [
            "Rebuild search as a hosted service first.",
            "Add a UI for reindex history."
        ],
        "file": "cli/reindex_search.py",
        "stale_file": "search/indexer.py",
        "extra_file": "tests/test_reindex_search.py",
        "file_hint": "the reindex CLI",
        "constraint": "Keep incremental reindexing; do not force full reindex on every run.",
        "constraint_hint": "the keep-incremental-reindex rule",
        "stale_constraint": "Always force a full reindex to avoid edge cases.",
        "extra_constraint": "Move reindexing into the frontend admin panel.",
        "detail": "The exact flag is `--index users_v2`.",
        "detail_hint": "the users_v2 index flag",
        "stale_detail": "The old flag was `--index users_legacy`.",
        "extra_detail": "The issue is a font mismatch in the search admin page.",
        "next_step": "Edit `cli/reindex_search.py` to preserve incremental mode and keep `--index users_v2`, then rerun `pytest tests/test_reindex_search.py -q`.",
        "next_step_distractors": [
            "Edit `search/indexer.py` and force full reindex on `users_legacy`.",
            "Ignore the CLI and build a reindex history UI."
        ],
        "completed": "The job queue submission and index existence check already work.",
        "open_issue": "The CLI dropped the exact target index flag.",
        "failure_mode": "lost exact CLI flag",
    },
    {
        "task_id": "bd06",
        "scenario": "Frontend build env injection",
        "goal": "Fix the frontend build so the API base URL is injected again.",
        "goal_distractors": [
            "Move the frontend to a different bundler first.",
            "Design a new settings page for build variables."
        ],
        "file": "frontend/build/config.ts",
        "stale_file": "frontend/src/config.ts",
        "extra_file": "frontend/.env.example",
        "file_hint": "the frontend build config",
        "constraint": "Keep the environment lookup at build time; do not hardcode the API URL.",
        "constraint_hint": "the build-time env lookup rule",
        "stale_constraint": "Hardcode the API URL in the source config file.",
        "extra_constraint": "Move configuration to localStorage first.",
        "detail": "The exact key is `VITE_API_BASE_URL`.",
        "detail_hint": "the Vite API base URL key",
        "stale_detail": "The old key was `API_BASE_URL`.",
        "extra_detail": "The actual bug is a misaligned button in the settings page.",
        "next_step": "Edit `frontend/build/config.ts` to preserve build-time injection of `VITE_API_BASE_URL`, then rerun `npm test -- --runInBand config`.",
        "next_step_distractors": [
            "Edit `frontend/src/config.ts` and hardcode `API_BASE_URL`.",
            "Ignore the build and redesign the settings page."
        ],
        "completed": "The fallback config object already works.",
        "open_issue": "The build step lost the exact environment key.",
        "failure_mode": "lost exact frontend env key",
    },
    {
        "task_id": "bd07",
        "scenario": "Cache invalidation helper",
        "goal": "Repair the cache invalidation helper so profile updates clear the right key.",
        "goal_distractors": [
            "Replace the cache layer with a completely new backend.",
            "Add a new admin page for cache stats."
        ],
        "file": "cache/invalidate_profile.py",
        "stale_file": "cache/client.py",
        "extra_file": "tests/test_invalidate_profile.py",
        "file_hint": "the profile cache invalidation helper",
        "constraint": "Keep the current key prefix; do not rename the cache namespace.",
        "constraint_hint": "the keep-cache-prefix rule",
        "stale_constraint": "Rename the cache namespace while fixing invalidation.",
        "extra_constraint": "Skip invalidation and shorten the TTL instead.",
        "detail": "The exact key format is `profile:{user_id}:summary`.",
        "detail_hint": "the profile summary cache key format",
        "stale_detail": "The old key format was `profiles:{user_id}`.",
        "extra_detail": "The issue is a CSS problem in the admin cache page.",
        "next_step": "Edit `cache/invalidate_profile.py` to keep the `profile:{user_id}:summary` key format and rerun `pytest tests/test_invalidate_profile.py -q`.",
        "next_step_distractors": [
            "Edit `cache/client.py` and rename the namespace to `profiles:{user_id}`.",
            "Ignore invalidation and build a cache stats page."
        ],
        "completed": "The Redis client and mutation hook already fire correctly.",
        "open_issue": "The helper now invalidates the wrong exact key.",
        "failure_mode": "lost exact cache key pattern",
    },
    {
        "task_id": "bd08",
        "scenario": "Test selection helper",
        "goal": "Restore the targeted test helper so smoke suites run quickly again.",
        "goal_distractors": [
            "Replace pytest with a new test framework first.",
            "Build a dashboard for flaky tests."
        ],
        "file": "tools/select_smoke_tests.py",
        "stale_file": "tools/run_tests.py",
        "extra_file": "tests/test_select_smoke_tests.py",
        "file_hint": "the smoke-test selection helper",
        "constraint": "Keep the helper deterministic; do not randomize test order.",
        "constraint_hint": "the deterministic-order rule",
        "stale_constraint": "Randomize smoke tests to spread coverage around.",
        "extra_constraint": "Run the full suite every time for consistency.",
        "detail": "The exact marker is `-m smoke and not slow`.",
        "detail_hint": "the smoke-not-slow marker expression",
        "stale_detail": "The old marker was `-m smoke`.",
        "extra_detail": "The issue is a typo in the testing dashboard title.",
        "next_step": "Edit `tools/select_smoke_tests.py` to preserve `-m smoke and not slow` and rerun `pytest tests/test_select_smoke_tests.py -q`.",
        "next_step_distractors": [
            "Edit `tools/run_tests.py` and randomize plain `-m smoke` runs.",
            "Ignore the helper and build a flaky-test dashboard."
        ],
        "completed": "The helper already reads changed-file input correctly.",
        "open_issue": "The exact marker expression was simplified too far.",
        "failure_mode": "lost exact test marker",
    },
]


NEXT_STEP_SPECS = [
    {
        "task_id": "ns01",
        "scenario": "Billing webhook rollout",
        "goal": "Finish the billing webhook rollout without repeating already completed setup work.",
        "goal_distractors": [
            "Build a billing analytics dashboard first.",
            "Replace billing webhooks with a polling job."
        ],
        "file": "billing/webhook_consumer.py",
        "stale_file": "billing/webhook_schema.py",
        "extra_file": "tests/test_webhook_consumer.py",
        "file_hint": "the webhook consumer module",
        "constraint": "Do not touch the already-migrated schema file.",
        "constraint_hint": "the schema work is already done",
        "stale_constraint": "Revisit the schema migration before touching runtime logic.",
        "extra_constraint": "Pause rollout and redesign webhook payloads.",
        "detail": "The remaining failing test is `tests/test_webhook_consumer.py::test_retries_409`.",
        "detail_hint": "the retry-on-409 test",
        "stale_detail": "The remaining issue is a schema migration hash mismatch.",
        "extra_detail": "The real problem is a chart legend in the billing UI.",
        "next_step": "Edit `billing/webhook_consumer.py` to handle the 409 retry path and rerun `pytest tests/test_webhook_consumer.py -q`.",
        "next_step_distractors": [
            "Re-edit `billing/webhook_schema.py` even though the migration is already done.",
            "Ignore the backend and build a billing analytics dashboard."
        ],
        "completed": "Schema migration, secret loading, and endpoint registration are already complete.",
        "open_issue": "Only the 409 retry behavior is still failing.",
        "failure_mode": "repeating completed schema work",
    },
    {
        "task_id": "ns02",
        "scenario": "Markdown export pipeline",
        "goal": "Finish the markdown export pipeline so scheduled exports stop failing.",
        "goal_distractors": [
            "Migrate exports to PDF first.",
            "Add a new export history page."
        ],
        "file": "exports/markdown_export.py",
        "stale_file": "exports/template_loader.py",
        "extra_file": "tests/test_markdown_export.py",
        "file_hint": "the markdown export worker",
        "constraint": "Template loading is already fixed; do not redo that part.",
        "constraint_hint": "template loading is already done",
        "stale_constraint": "Rework template loading again before touching runtime output.",
        "extra_constraint": "Pause exports and only add a history page.",
        "detail": "The remaining issue is the missing `front_matter` block.",
        "detail_hint": "the missing front matter block",
        "stale_detail": "The remaining issue is a broken template path.",
        "extra_detail": "The actual problem is a color mismatch in the export page.",
        "next_step": "Edit `exports/markdown_export.py` to restore the `front_matter` block and rerun `pytest tests/test_markdown_export.py -q`.",
        "next_step_distractors": [
            "Re-edit `exports/template_loader.py` even though template loading already works.",
            "Ignore the worker and build an export history page."
        ],
        "completed": "Template lookup, scheduler wiring, and storage writes are already fixed.",
        "open_issue": "Only the output formatting step is still broken.",
        "failure_mode": "repeating completed template work",
    },
    {
        "task_id": "ns03",
        "scenario": "Notification digest job",
        "goal": "Finish the notification digest job so daily digests send once per user.",
        "goal_distractors": [
            "Create a whole new notification center UI.",
            "Replace the digest job with a third-party product."
        ],
        "file": "jobs/daily_digest.py",
        "stale_file": "jobs/query_digest_candidates.py",
        "extra_file": "tests/test_daily_digest.py",
        "file_hint": "the daily digest job",
        "constraint": "Candidate selection is already correct; do not revisit that query.",
        "constraint_hint": "candidate selection is already done",
        "stale_constraint": "Revisit the candidate selection query before handling sends.",
        "extra_constraint": "Pause digests and focus on a new UI.",
        "detail": "The remaining failing case is duplicate sends for `user_id=42`.",
        "detail_hint": "the duplicate send for user 42",
        "stale_detail": "The remaining issue is an empty candidate list.",
        "extra_detail": "The real issue is the spacing in the notification center mockup.",
        "next_step": "Edit `jobs/daily_digest.py` to prevent duplicate sends for `user_id=42` and rerun `pytest tests/test_daily_digest.py -q`.",
        "next_step_distractors": [
            "Re-edit `jobs/query_digest_candidates.py` even though the query is already correct.",
            "Ignore the backend and build a notification center UI."
        ],
        "completed": "Candidate selection, template rendering, and enqueue logic are already working.",
        "open_issue": "Only the duplicate-send guard is still missing.",
        "failure_mode": "repeating completed query work",
    },
    {
        "task_id": "ns04",
        "scenario": "Role sync command",
        "goal": "Finish the role sync command so stale group memberships stop persisting.",
        "goal_distractors": [
            "Build a new admin page for roles first.",
            "Replace the role system with an external provider."
        ],
        "file": "cli/sync_roles.py",
        "stale_file": "auth/role_mapping.py",
        "extra_file": "tests/test_sync_roles.py",
        "file_hint": "the role sync CLI",
        "constraint": "Role mapping is already correct; do not redo that table.",
        "constraint_hint": "role mapping is already done",
        "stale_constraint": "Rework the role mapping table before touching the sync path.",
        "extra_constraint": "Pause sync work and redesign role management.",
        "detail": "The remaining issue is that removed groups still leave `editor` assignments behind.",
        "detail_hint": "the stale editor assignment issue",
        "stale_detail": "The remaining issue is a missing role mapping entry.",
        "extra_detail": "The actual problem is a typo in the admin page heading.",
        "next_step": "Edit `cli/sync_roles.py` to clear stale `editor` assignments and rerun `pytest tests/test_sync_roles.py -q`.",
        "next_step_distractors": [
            "Re-edit `auth/role_mapping.py` even though the mapping table is already correct.",
            "Ignore the CLI and redesign role management."
        ],
        "completed": "The mapping table, dry-run mode, and group fetch already work.",
        "open_issue": "Only stale assignment cleanup is still missing.",
        "failure_mode": "repeating completed mapping work",
    },
    {
        "task_id": "ns05",
        "scenario": "Theme asset cache refresh",
        "goal": "Finish the theme asset cache refresh so new logos appear after publish.",
        "goal_distractors": [
            "Rebuild the entire theming system first.",
            "Create a theme preview gallery."
        ],
        "file": "themes/refresh_assets.py",
        "stale_file": "themes/upload_assets.py",
        "extra_file": "tests/test_refresh_assets.py",
        "file_hint": "the theme asset refresh job",
        "constraint": "Uploads already work; do not revisit the upload path.",
        "constraint_hint": "uploads are already done",
        "stale_constraint": "Redo uploads before touching refresh invalidation.",
        "extra_constraint": "Stop the refresh job and focus on a theme gallery.",
        "detail": "The remaining issue is the stale cache key for `logo_dark.svg`.",
        "detail_hint": "the stale logo_dark cache key",
        "stale_detail": "The remaining issue is a missing upload form field.",
        "extra_detail": "The actual problem is a layout mismatch in the gallery.",
        "next_step": "Edit `themes/refresh_assets.py` to invalidate the stale `logo_dark.svg` cache key and rerun `pytest tests/test_refresh_assets.py -q`.",
        "next_step_distractors": [
            "Re-edit `themes/upload_assets.py` even though uploads already work.",
            "Ignore the refresh job and build a theme preview gallery."
        ],
        "completed": "Uploads, manifest writes, and publish hooks are already complete.",
        "open_issue": "Only cache invalidation for the new logo still fails.",
        "failure_mode": "repeating completed upload work",
    },
    {
        "task_id": "ns06",
        "scenario": "Slack notifier retry flow",
        "goal": "Finish the Slack notifier retry flow so transient API failures recover cleanly.",
        "goal_distractors": [
            "Replace Slack notifications with email only.",
            "Design a new incident dashboard."
        ],
        "file": "notifications/slack_notifier.py",
        "stale_file": "notifications/message_builder.py",
        "extra_file": "tests/test_slack_notifier.py",
        "file_hint": "the Slack notifier runtime",
        "constraint": "Message formatting already works; do not rewrite the builder.",
        "constraint_hint": "message formatting is already done",
        "stale_constraint": "Rewrite the message builder again before touching retries.",
        "extra_constraint": "Pause Slack work and build an incident dashboard.",
        "detail": "The remaining failure is a missing retry on `429 Too Many Requests`.",
        "detail_hint": "the missing retry on 429",
        "stale_detail": "The remaining failure is bad markdown formatting.",
        "extra_detail": "The actual issue is a chart label in the incident dashboard.",
        "next_step": "Edit `notifications/slack_notifier.py` to add a retry for `429 Too Many Requests` and rerun `pytest tests/test_slack_notifier.py -q`.",
        "next_step_distractors": [
            "Re-edit `notifications/message_builder.py` even though formatting already works.",
            "Ignore the notifier and build an incident dashboard."
        ],
        "completed": "Webhook loading, channel selection, and message formatting already work.",
        "open_issue": "Only retry behavior on transient failures is still missing.",
        "failure_mode": "repeating completed formatting work",
    },
    {
        "task_id": "ns07",
        "scenario": "Audit log redaction",
        "goal": "Finish audit log redaction so secrets stop leaking into stored events.",
        "goal_distractors": [
            "Create an audit log viewer UI first.",
            "Replace the entire audit system with a vendor product."
        ],
        "file": "audit/redact_events.py",
        "stale_file": "audit/write_events.py",
        "extra_file": "tests/test_redact_events.py",
        "file_hint": "the audit redaction helper",
        "constraint": "Event writing already works; do not touch the writer unless needed.",
        "constraint_hint": "event writing is already done",
        "stale_constraint": "Rebuild the writer before touching redaction rules.",
        "extra_constraint": "Pause redaction work and build a log viewer.",
        "detail": "The remaining missing rule is redacting `authorization` headers.",
        "detail_hint": "the authorization-header redaction rule",
        "stale_detail": "The remaining issue is a write timeout in the event writer.",
        "extra_detail": "The actual issue is the viewer color palette.",
        "next_step": "Edit `audit/redact_events.py` to redact `authorization` headers and rerun `pytest tests/test_redact_events.py -q`.",
        "next_step_distractors": [
            "Re-edit `audit/write_events.py` even though event writing already works.",
            "Ignore redaction and build an audit log viewer."
        ],
        "completed": "Event writing, storage, and rotation already work.",
        "open_issue": "Only the redaction rule set still needs the final header case.",
        "failure_mode": "repeating completed writer work",
    },
    {
        "task_id": "ns08",
        "scenario": "Image thumbnail worker",
        "goal": "Finish the thumbnail worker so portrait uploads stop cropping faces.",
        "goal_distractors": [
            "Build a whole new media gallery UI.",
            "Switch all image processing to a hosted service."
        ],
        "file": "media/thumbnail_worker.py",
        "stale_file": "media/upload_handler.py",
        "extra_file": "tests/test_thumbnail_worker.py",
        "file_hint": "the thumbnail worker",
        "constraint": "Upload handling already works; do not revisit the uploader.",
        "constraint_hint": "upload handling is already done",
        "stale_constraint": "Redo upload handling before touching resizing logic.",
        "extra_constraint": "Pause worker fixes and design a media gallery.",
        "detail": "The remaining failing case is the portrait crop preset `cover_portrait`.",
        "detail_hint": "the failing cover_portrait preset",
        "stale_detail": "The remaining issue is a missing upload MIME check.",
        "extra_detail": "The actual issue is a spacing bug in the gallery page.",
        "next_step": "Edit `media/thumbnail_worker.py` to fix the `cover_portrait` crop path and rerun `pytest tests/test_thumbnail_worker.py -q`.",
        "next_step_distractors": [
            "Re-edit `media/upload_handler.py` even though uploads already work.",
            "Ignore the worker and design a media gallery."
        ],
        "completed": "Upload handling, file persistence, and job enqueueing already work.",
        "open_issue": "Only the portrait crop preset still fails.",
        "failure_mode": "repeating completed uploader work",
    },
]


LABELS = ["A", "B", "C"]
POSITION_PATTERNS = [
    {"goal": "A", "file": "B", "constraint": "C", "detail": "B", "next_step": "A"},
    {"goal": "B", "file": "C", "constraint": "A", "detail": "C", "next_step": "B"},
    {"goal": "C", "file": "A", "constraint": "B", "detail": "A", "next_step": "C"},
    {"goal": "A", "file": "C", "constraint": "B", "detail": "C", "next_step": "B"},
    {"goal": "B", "file": "A", "constraint": "C", "detail": "A", "next_step": "C"},
    {"goal": "C", "file": "B", "constraint": "A", "detail": "B", "next_step": "A"},
]


def make_candidate_set(correct: str, distractors: list[str], correct_label: str) -> list[dict[str, str]]:
    value_by_label = {}
    distractor_iter = iter(distractors[:2])
    for label in LABELS:
        if label == correct_label:
            value_by_label[label] = correct
        else:
            value_by_label[label] = next(distractor_iter)
    return [{"id": label, "text": value_by_label[label]} for label in LABELS]


def generic_prefix(spec: dict[str, str], family_note: str) -> list[dict[str, str]]:
    return [
        {"speaker": "user", "text": f"We need to finish the {spec['scenario'].lower()}. {spec['goal']}"},
        {"speaker": "assistant", "text": f"My first pass was to work in `{spec['stale_file']}` and follow this rule: {spec['stale_constraint']}"},
        {"speaker": "tool", "text": f"Status note: {spec['completed']}"},
        {"speaker": "user", "text": f"Do not lose the key detail from this task: {spec['detail']}"},
        {"speaker": "assistant", "text": f"Understood. The remaining blocker seems to be: {spec['open_issue']}"},
        {"speaker": "user", "text": f"Correction: the active file is actually `{spec['file']}`. Also, the latest rule is: {spec['constraint']}"},
        {"speaker": "assistant", "text": f"Thanks. I will update the plan around `{spec['file']}` and keep in mind that {family_note}"},
        {"speaker": "tool", "text": f"Open issue recap: {spec['open_issue']}"},
    ]


def build_task(spec: dict[str, str], family: str, family_note: str, pattern: dict[str, str]) -> dict[str, object]:
    candidate_sets = {
        "goal": make_candidate_set(spec["goal"], spec["goal_distractors"], pattern["goal"]),
        "file": make_candidate_set(spec["file"], [spec["stale_file"], spec["extra_file"]], pattern["file"]),
        "constraint": make_candidate_set(spec["constraint"], [spec["stale_constraint"], spec["extra_constraint"]], pattern["constraint"]),
        "detail": make_candidate_set(spec["detail"], [spec["stale_detail"], spec["extra_detail"]], pattern["detail"]),
        "next_step": make_candidate_set(spec["next_step"], spec["next_step_distractors"], pattern["next_step"]),
    }
    return {
        "task_id": spec["task_id"],
        "family": family,
        "scenario": spec["scenario"],
        "failure_mode": spec["failure_mode"],
        "prefix_turns": generic_prefix(spec, family_note),
        "recent_turns": RECENT_TURNS,
        "candidate_sets": candidate_sets,
        "gold": {
            "goal": pattern["goal"],
            "file": pattern["file"],
            "constraint": pattern["constraint"],
            "detail": pattern["detail"],
            "next_step": pattern["next_step"],
        },
        "state": {
            "active_goal": spec["goal"],
            "target_file": spec["file"],
            "target_file_hint": spec["file_hint"],
            "latest_constraint": spec["constraint"],
            "latest_constraint_hint": spec["constraint_hint"],
            "key_exact_detail": spec["detail"],
            "key_exact_detail_hint": spec["detail_hint"],
            "next_step": spec["next_step"],
            "completed_work": spec["completed"],
            "open_issue": spec["open_issue"],
        },
    }


def generate_tasks() -> list[dict[str, object]]:
    tasks: list[dict[str, object]] = []
    all_specs = [
        (LATEST_CONSTRAINT_SPECS, "latest_constraint", "the latest correction overrides the earlier plan."),
        (BRITTLE_DETAIL_SPECS, "brittle_detail", "the exact brittle detail matters more than the earlier rough description."),
        (NEXT_STEP_SPECS, "next_step_continuity", "some earlier setup work is already finished, so the next action should not repeat it."),
    ]
    idx = 0
    for spec_group, family, note in all_specs:
        for spec in spec_group:
            pattern = POSITION_PATTERNS[idx % len(POSITION_PATTERNS)]
            tasks.append(build_task(spec, family, note, pattern))
            idx += 1
    hard_sources = ["lc01", "lc02", "bd01", "bd02", "ns01", "ns02"]
    by_id = {task["task_id"]: task for task in tasks}
    for task_id in hard_sources:
        tasks.append(make_hard_variant(by_id[task_id]))
    return tasks


def lookup_option_text(task: dict[str, object], field: str, label: str) -> str:
    for option in task["candidate_sets"][field]:
        if option["id"] == label:
            return option["text"]
    raise KeyError(label)


def first_wrong_label(task: dict[str, object], field: str) -> str:
    gold = task["gold"][field]
    for option in task["candidate_sets"][field]:
        if option["id"] != gold:
            return option["id"]
    raise ValueError(field)


def make_hard_variant(base_task: dict[str, object]) -> dict[str, object]:
    task = deepcopy(base_task)
    wrong_file = lookup_option_text(task, "file", first_wrong_label(task, "file"))
    wrong_constraint = lookup_option_text(task, "constraint", first_wrong_label(task, "constraint"))
    wrong_detail = lookup_option_text(task, "detail", first_wrong_label(task, "detail"))
    wrong_next = lookup_option_text(task, "next_step", first_wrong_label(task, "next_step"))

    task["task_id"] = f"{task['task_id']}_hard"
    task["scenario"] = f"{task['scenario']} hard variant"
    task["failure_mode"] = f"{task['failure_mode']} plus multiple stale branches"

    prefix = deepcopy(task["prefix_turns"])
    insert_block = [
        {"speaker": "assistant", "text": f"Interim branch note: I briefly switched to `{wrong_file}` and followed this now-obsolete rule: {wrong_constraint}"},
        {"speaker": "tool", "text": f"Legacy scratch note that should now be ignored: {wrong_detail}"},
        {"speaker": "user", "text": "That interim branch is stale. Do not keep the temporary file, stale rule, or legacy scratch note."},
        {"speaker": "assistant", "text": f"Understood. I will discard the stale branch and I will not follow this outdated next step: {wrong_next}"},
    ]
    task["prefix_turns"] = prefix[:5] + insert_block + prefix[5:]
    task["recent_turns"] = [
        {
            "speaker": "user",
            "text": (
                f"I found a stale reminder from an abandoned branch. It says to work in `{wrong_file}` "
                f"and to use this old direction: {wrong_constraint}"
            ),
        },
        {"speaker": "tool", "text": f"Stale reminder detail that may be wrong: {wrong_detail}"},
        {
            "speaker": "assistant",
            "text": (
                "That note looks stale. I should not trust the reminder file, rule, detail, or next step "
                "until I reconcile it with the earlier session."
            ),
        },
        {
            "speaker": "user",
            "text": (
                "Exactly. Recover the real final state from the earlier context, not the stale reminder, "
                "before you continue."
            ),
        },
        {
            "speaker": "assistant",
            "text": f"I will ignore the stale reminder unless the earlier context confirms this old next step: {wrong_next}",
        },
    ]
    return task


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the synthetic context-compaction benchmark.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    tasks = generate_tasks()
    dump_json(args.output, tasks)
    print(f"Wrote {len(tasks)} tasks to {args.output}")


if __name__ == "__main__":
    main()
