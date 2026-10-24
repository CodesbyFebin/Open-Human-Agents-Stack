#!/usr/bin/env bash
set -Eeuo pipefail

REPO="CodesbyFebin/Open-Human-Agents-Stack"
PROJECT="OpenMinds"
WORKDIR="${OPENMINDS_WORKDIR:-$PWD/Open-Human-Agents-Stack}"
MODE="${1:-setup}"

log() {
  printf '\n[OpenMinds] %s\n' "$*"
}

fail() {
  printf '\n[FAILED] %s\n' "$*" >&2
  exit 1
}

need() {
  command -v "$1" >/dev/null 2>&1 ||
    fail "Required command missing: $1"
}

check_tools() {
  need gh
  need git
  need bash
  gh auth status >/dev/null 2>&1 ||
    fail "Run: gh auth login"
}

prepare_repo() {
  if [[ ! -d "$WORKDIR/.git" ]]; then
    log "Cloning $REPO"
    gh repo clone "$REPO" "$WORKDIR"
  fi

  cd "$WORKDIR"

  local origin
  origin="$(git remote get-url origin)"

  case "$origin" in
    *CodesbyFebin/Open-Human-Agents-Stack*)
      ;;
    *)
      fail "Unexpected repository origin: $origin"
      ;;
  esac

  if [[ -n "$(git status --porcelain)" ]]; then
    fail "Working tree has uncommitted changes."
  fi
}

ensure_label() {
  local name="$1"
  local color="$2"

  gh label create "$name" \
    --repo "$REPO" \
    --color "$color" \
    --force >/dev/null
}

ensure_issue() {
  local title="$1"
  local label="$2"
  local body="$3"

  local existing
  existing="$(
    gh issue list \
      --repo "$REPO" \
      --state all \
      --limit 200 \
      --json title \
      --jq ".[] | select(.title == \"$title\") | .title"
  )"

  if [[ -n "$existing" ]]; then
    log "Already tracked: $title"
    return
  fi

  gh issue create \
    --repo "$REPO" \
    --title "$title" \
    --label "$label" \
    --body "$body"
}

setup_labels() {
  log "Configuring development labels"

  ensure_label "phase:P0" "B60205"
  ensure_label "phase:P1" "D93F0B"
  ensure_label "phase:P2" "FBCA04"
  ensure_label "phase:P3" "0E8A16"
  ensure_label "security" "B60205"
  ensure_label "verification" "5319E7"
  ensure_label "release-blocker" "D73A4A"
}

setup_issues() {
  log "Creating implementation backlog"

  ensure_issue \
    "P0: Build complete FastAPI and Next.js application" \
    "phase:P0" \
    "Implement missing source modules, frontend components, Dockerfiles, health checks, application configuration and executable CI.

Acceptance:
- Backend imports and starts successfully
- Frontend production build passes
- Docker Compose starts all required services
- No fake telemetry or success responses
- Automated tests pass"

  ensure_issue \
    "P0: PostgreSQL persistence, migrations and recovery" \
    "phase:P0" \
    "Implement versioned database migrations, durable entities, transactional writes and backup/restore.

Acceptance:
- Migrations apply to fresh PostgreSQL
- Concurrent writes are tested
- Database recovery is demonstrated
- No application state depends on in-memory placeholders"

  ensure_issue \
    "P0: Authentication, authorization and tenant isolation" \
    "phase:P0" \
    "Implement real authentication, session lifecycle, RBAC, tenant ownership checks, CSRF protection where applicable and audit records.

Acceptance:
- Anonymous privileged calls fail
- Cross-tenant access fails
- Session expiration and revocation work
- Authorization integration tests pass"

  ensure_issue \
    "P1: Durable isolated coding workers" \
    "phase:P1" \
    "Implement durable task queues, isolated execution, bounded resources, retry policies, timeouts, cancellation and crash recovery.

Acceptance:
- Jobs survive API restarts
- Workers enforce CPU, memory and filesystem limits
- Cancellation terminates the execution tree
- Hostile execution tests pass"

  ensure_issue \
    "P1: Capability-controlled MCP execution" \
    "phase:P1" \
    "Implement MCP server discovery, tool schemas, per-agent grants, exact-action approvals, execution limits and audit logging.

Acceptance:
- Unauthorized tools are rejected
- Tool inputs are validated
- Privileged actions require approval
- Every execution receives evidence records"

  ensure_issue \
    "P2: Persistent human-agent collaboration" \
    "phase:P2" \
    "Implement organizations, agent identities, missions, tasks, assignments, human handoffs, approvals and live board state.

Acceptance:
- Multi-user collaboration works
- All board data is persisted
- Actions enforce ownership and permissions
- Browser end-to-end tests pass"

  ensure_issue \
    "P2: Workflow editor and evidence dashboard" \
    "phase:P2" \
    "Implement versioned workflow DAGs, validated transitions, execution history, diffs, artifacts, approvals and live telemetry.

Acceptance:
- Invalid workflow graphs are rejected
- Executions are traceable
- Dashboard metrics come from real events
- Evidence is queryable and verifiable"

  ensure_issue \
    "P3: Security and operational qualification" \
    "phase:P3" \
    "Implement and execute API, database, worker, MCP, browser, security and recovery tests.

Acceptance:
- CI checks pass on the release commit
- Hostile execution tests pass
- Backup restoration is verified
- Staging deployment is validated
- Independent security review is recorded"

  log "Implementation backlog created."
}

check_file() {
  local file="$1"
  [[ -s "$file" ]] ||
    fail "Missing or empty required file: $file"
}

run_gates() {
  prepare_repo

  log "Checking required source files"

  check_file "backend/main.py"
  check_file "package.json"
  check_file "requirements.txt"
  check_file "Dockerfile.backend"
  check_file "Dockerfile.frontend"
  check_file ".github/workflows/ci.yml"

  log "Checking for known placeholder behavior"

  if rg -n \
    'active_runners["'\'']?: 12|cost_usd_today["'\'']?: 4\.27|trajectories["'\'']?: 148' \
    backend; then
    fail "Hardcoded operational telemetry remains."
  fi

  log "Checking implementation directories"

  [[ -d backend/pipeline ]] ||
    fail "Pipeline implementation missing."

  [[ -d agents ]] ||
    fail "Agent implementation missing."

  [[ -d database ]] ||
    fail "Database implementation missing."

  [[ -d tests ]] ||
    fail "Automated test directory missing."

  log "Running Python tests"

  need pytest
  pytest -q

  log "Running frontend checks"

  need npm
  npm ci
  npm run build

  log "Checking Docker configuration"

  need docker
  docker compose \
    -f docker/docker-compose.yml \
    config --quiet

  log "Checking GitHub CI"

  local branch
  branch="$(git branch --show-current)"

  gh run list \
    --repo "$REPO" \
    --branch "$branch" \
    --limit 5

  log "Local checks completed."
  log "External security and staging gates still require evidence."
}

show_status() {
  log "GitHub implementation issues"

  gh issue list \
    --repo "$REPO" \
    --state all \
    --limit 100 \
    --json number,title,state,labels \
    --jq '.[] | "\(.number) [\(.state)] \(.title)"'

  log "Recent workflow results"

  gh run list \
    --repo "$REPO" \
    --limit 10
}

check_tools

case "$MODE" in
  setup)
    prepare_repo
    setup_labels
    setup_issues
    show_status
    ;;
  verify)
    need rg
    run_gates
    ;;
  status)
    show_status
    ;;
  *)
    printf 'Usage: %s {setup|verify|status}\n' "$0"
    exit 2
    ;;
esac
