#!/usr/bin/env bash
# Instalación desde cero en una máquina nueva (ambiente dev). En qa y prod: make deploy en el servidor.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT/.env" ] || { cp "$ROOT/.env.dev" "$ROOT/.env"; echo "Creé .env desde .env.dev: pon tu llave de Stripe en él."; }
source "$(dirname "$0")/common.sh"
cd "$ROOT"
[ "$CAMPUS_ENV" = dev ] || { echo ".env es de $CAMPUS_ENV: en el servidor se usa make deploy." >&2; exit 1; }

ensure_venv
apply_config
apply_plugins
apply_mounts
"$TUTOR" dev launch --non-interactive

echo
echo "Listo. LMS: http://local.openedx.io:8000  Studio: http://studio.local.openedx.io:8001"
echo "CMS: http://campus-cms.local.openedx.io:8010/api/health/"
echo "Crea tu admin con: make admin, y dale acceso a /admin de Campus con: make contador USER_NAME=admin"
