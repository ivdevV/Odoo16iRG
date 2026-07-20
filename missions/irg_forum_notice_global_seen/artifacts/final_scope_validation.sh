#!/usr/bin/env bash
set -euo pipefail

main_compose="/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/docker-compose.local.yml"

git diff --check
expected_porcelain="?? .agents/knowledge/odoo_development_modding/artifacts/forum_notice_global_seen.md
?? addons-extra/extrairg/irg_forum_notice_global_seen/
?? missions/irg_forum_notice_global_seen/"
actual_porcelain="$(git status --porcelain=v1 --untracked-files=normal)"
test "$actual_porcelain" = "$expected_porcelain"
test -z "$(find addons-extra/extrairg/irg_forum_notice_global_seen \
  -type d -name __pycache__ -print)"
docker compose -f "$main_compose" ps
expected_services="odoo_local
pgodoo_local
redisodoo_local"
actual_services="$(docker compose -f "$main_compose" \
  ps --services --status running | sort)"
test "$actual_services" = "$expected_services"
docker inspect odoo16irg_local --format \
  '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}' \
  | rg -q '^/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/addons-extra -> /mnt/extra-addons$'
test -z "$(docker ps --format '{{.Names}}' | rg 'odoo16irg_local-odoo_local-run' || true)"
if curl -fsS --max-time 2 http://127.0.0.1:18069 >/dev/null; then
  exit 1
fi
git status --short --branch
echo 'final_scope_cleanup_shared_service: PASS'
