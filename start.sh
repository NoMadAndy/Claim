#!/usr/bin/env bash
set -uo pipefail  # Removed -e to allow recovery from transient errors like pip failures
trap 'echo "[error] Script failed at line $LINENO"; exit 1' ERR

# Simple bootstrap/start script for Claim (backend + static frontend)
# Requirements: Python 3.10+, PostgreSQL/PostGIS (matching DATABASE_URL), internet for pip on first run.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
REQ_FILE="$PROJECT_ROOT/requirements.txt"

# Default settings (override via environment)
: "${HOST:=0.0.0.0}"
: "${PORT:=8000}"
: "${WORKERS:=1}"
: "${RELOAD:=false}"

# DB bootstrap via Docker Compose (PostGIS)
: "${USE_COMPOSE_DB:=true}"
: "${DB_USER:=claim_user}"
: "${DB_PASSWORD:=claim_password}"
: "${DB_NAME:=claim_db}"
: "${DB_PORT:=5432}"

# Ensure DATABASE_URL is set; otherwise try to use local Compose PostGIS or fallback to config default
: "${DATABASE_URL:=}"

compose_cmd=""
# Prefer classic docker-compose if present
if command -v docker-compose >/dev/null 2>&1; then
  compose_cmd="docker-compose"
elif command -v docker >/dev/null 2>&1; then
  # Check if docker compose plugin is available
  if docker compose version >/dev/null 2>&1; then
    compose_cmd="docker compose"
  fi
fi

if [[ -z "$DATABASE_URL" && "$USE_COMPOSE_DB" == "true" && -n "$compose_cmd" ]]; then
  compose_target_url="postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}"
  echo "[info] Using Docker Compose PostGIS database at $compose_target_url"
  # Check if Docker daemon is running
  if ! docker info >/dev/null 2>&1; then
    echo "[error] Docker-Daemon läuft nicht oder ist nicht erreichbar!" >&2
    echo "[hint] Starte Docker manuell (z.B. 'sudo systemctl start docker' oder 'service docker start')." >&2
    echo "[hint] Prüfe ggf. 'docker context ls' und 'docker context use default'." >&2
    echo "[hint] Prüfe Umgebungsvariable DOCKER_HOST (sollte meist unset sein oder auf unix:///var/run/docker.sock zeigen)." >&2
    exit 1
  fi
  set +e
  (cd "$PROJECT_ROOT" && $compose_cmd up -d db)
  compose_status=$?
  set -e
  if [[ $compose_status -eq 0 ]]; then
    export DATABASE_URL="$compose_target_url"
  else
    echo "[error] Failed to start PostGIS via Compose (status $compose_status)." >&2
    echo "[error] Bitte prüfe Docker-Status, DOCKER_HOST und Berechtigungen." >&2
    compose_cmd=""
    DATABASE_URL=""
    exit 1
  fi
fi

if [[ -z "$DATABASE_URL" ]]; then
  if [[ "$USE_COMPOSE_DB" == "true" && -z "$compose_cmd" ]]; then
    echo "[error] Docker/compose not available and DATABASE_URL not set. Please set DATABASE_URL to a reachable PostGIS instance." >&2
    exit 1
  else
    echo "[warn] DATABASE_URL not set. Using default from app/config.py (may fail if DB not available)."
  fi
fi

echo "[info] Using host=$HOST port=$PORT workers=$WORKERS reload=$RELOAD"

# Create venv if missing
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[info] Creating virtual environment at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# Activate venv
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# Upgrade pip & install deps (use --break-system-packages on Debian-based systems)
echo "[info] Installing dependencies..."
pip install --upgrade pip --break-system-packages >/dev/null 2>&1 || true
pip install -r "$REQ_FILE" --break-system-packages
echo "[info] Dependencies installed successfully"

# Wait for database if applicable
if [[ "$DATABASE_URL" == postgresql* ]]; then
  echo "[info] Waiting for database ..."
  set +e
  python3 - <<'PY'
import os, time, sys
try:
    import psycopg2
    url = os.environ.get("DATABASE_URL")
    for i in range(20):
        try:
            conn = psycopg2.connect(dsn=url, connect_timeout=3)
            conn.close()
            print("[info] Database is ready")
            sys.exit(0)
        except Exception as e:
            print(f"[info] DB not ready yet ({i+1}/20): {e}")
            time.sleep(1)
    print("[error] Database not reachable after retries")
    sys.exit(1)
except ImportError:
    print("[warn] psycopg2 not available, skipping DB check")
    sys.exit(0)
PY
  db_check=$?
  set -e
  if [[ $db_check -ne 0 && $db_check -ne 0 ]]; then
    echo "[warn] Database check inconclusive, continuing anyway..."
  fi
fi

# Run migrations/init (handled in app.lifespan via init_db)

# Start server
UVICORN_CMD=(uvicorn app.main:app --host "$HOST" --port "$PORT" --workers "$WORKERS")
if [[ "$RELOAD" == "true" ]]; then
  UVICORN_CMD+=(--reload)
fi

echo "[info] Starting uvicorn..."
exec "${UVICORN_CMD[@]}"
