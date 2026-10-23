#!/bin/bash
# Idempotent repository bootstrap. Starts Docker only long enough to pull
# the local images, then stops it. The daemon belongs to start.sh.
set -eu
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
bash "$ROOT/.cursor/materialize-compose.sh" "$ROOT"
if ! command -v docker >/dev/null 2>&1; then
  sudo bash "$ROOT/.cursor/install-docker-packages.sh"
fi
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
sudo docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml pull
sudo service docker stop || true
if [ -f /var/run/docker.pid ]; then
  sudo kill "$(cat /var/run/docker.pid)" || true
fi
sleep 1
