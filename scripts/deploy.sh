#!/usr/bin/env bash
# En el servidor (dev, qa o prod), lo único que se corre: make deploy
#   1. Baja el código (git pull y submódulos).
#   2. Instala Tutor si falta y aplica .env.
#   3. Baja las imágenes del registro, genera el docker compose y enciende todo con `tutor local`.
# La primera vez inicializa todo (migraciones, CMS, cuenta de servicio); después actualiza.
cd "$(dirname "$0")/.."
# git pull puede cambiar este mismo script: después de bajar el código se corre la versión nueva.
if [ -z "${CAMPUS_DEPLOY_PULLED:-}" ]; then
  git pull --ff-only
  git submodule update --init --recursive
  CAMPUS_DEPLOY_PULLED=1 exec scripts/deploy.sh "$@"
fi
source scripts/common.sh
cd "$ROOT"

command -v docker >/dev/null || { echo "Instala Docker Engine: https://docs.docker.com/engine/install/" >&2; exit 1; }
[ -f .env ] || { echo "Falta .env: cp .env.dev .env (o .env.qa, .env.prod) y llena sus llaves" >&2; exit 1; }
[ "$MODE" = local ] || { echo ".env es de local: en el servidor copia .env.dev, .env.qa o .env.prod (en tu máquina usa make setup)" >&2; exit 1; }
# Las llaves de la plantilla terminan en ...: si queda alguna, falta llenarla.
if read_kv .env | grep -E '\.\.\.$'; then
  echo "Llena en .env los valores de arriba (siguen como en la plantilla)." >&2; exit 1
fi
ensure_venv
# Primero los plugins: sus valores por omisión (CAMPUS_WEB_URL...) los usa la configuración.
apply_plugins
apply_config
# En el VPS no hay código fuente: todo viene en las imágenes.
"$TUTOR" config save --set 'MOUNTS=[]'
"$TUTOR" images pull "${SERVER_IMAGES[@]}"
# launch: genera el docker compose, lo enciende, migra e inicializa (CMS, cuenta de servicio...).
"$TUTOR" local launch --non-interactive
# Los contenedores con configuración nueva se recrean; los demás se reinician para tomar el código nuevo.
"$TUTOR" local restart
echo
echo "$CAMPUS_ENV encendido:"
echo "  Campus:  $("$TUTOR" config printvalue CAMPUS_WEB_URL)"
echo "  LMS:     https://$("$TUTOR" config printvalue LMS_HOST)"
echo "  Studio:  https://$("$TUTOR" config printvalue CMS_HOST)"
echo "  CMS:     https://$("$TUTOR" config printvalue CAMPUS_CMS_HOST)/api/health/"
