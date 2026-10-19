#!/usr/bin/env bash
# Seed config.toml from the environment, then serve the WebUI behind Caddy's access-key gate.
set -euo pipefail

# Fail closed: an empty key would let "?key=" through the gate
if [[ ! "${MPT_ACCESS_KEY:-}" =~ ^[A-Za-z0-9_-]{16,}$ ]]; then
  echo "MPT_ACCESS_KEY must be 16+ URL-safe characters (A-Z a-z 0-9 _ -)" >&2
  exit 1
fi

python /app/deploy/seed_config.py
mpt webui --host 127.0.0.1 --port 8501 --headless &
caddy run --config /app/deploy/Caddyfile --adapter caddyfile &

# Exit when either process dies so the platform restarts the container
wait -n
exit 1
