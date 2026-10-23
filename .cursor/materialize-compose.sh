#!/bin/bash
# Copy the local compose template into docker-compose.local.yml.
# A file whose first line is not the sentinel is left untouched.
set -eu
ROOT="$1"
DEST="$ROOT/docker-compose.local.yml"
TEMPLATE="$ROOT/.cursor/runtime/odoo-local-compose.yml"
SENTINEL="# cursor-cloud-runtime-generated: odoo16irg-local-v1"
if [ -f "$DEST" ]; then
  FIRST="$(head -n 1 "$DEST")"
  if [ "$FIRST" != "$SENTINEL" ]; then
    exit 0
  fi
fi
cp "$TEMPLATE" "$DEST"
