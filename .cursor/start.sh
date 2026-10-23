#!/bin/bash
# Per-boot startup. Re-entrant. Brings up Docker and local Postgres only.
set -eu
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
bash "$ROOT/.cursor/materialize-compose.sh" "$ROOT"
if ! sudo docker info >/dev/null 2>&1; then
  sudo service docker start || true
  if ! sudo docker info >/dev/null 2>&1; then
    sudo sh -c 'dockerd >/tmp/dockerd.log 2>&1 &'
    i=0
    while [ "$i" -lt 60 ]; do
      if sudo docker info >/dev/null 2>&1; then
        break
      fi
      i=$((i + 1))
      sleep 1
    done
  fi
fi
sudo docker info >/dev/null
sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml up -d pgodoo_local
i=0
while [ "$i" -lt 60 ]; do
  status="$(sudo docker inspect --format '{{.State.Health.Status}}' pgodoo16irg_local 2>/dev/null || true)"
  if [ "$status" = "healthy" ]; then
    exit 0
  fi
  i=$((i + 1))
  sleep 2
done
echo "pgodoo16irg_local did not become healthy" >&2
exit 1
