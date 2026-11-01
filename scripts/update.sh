#!/usr/bin/env bash
# Trae los cambios del equipo y los aplica. Se corre después de cada git pull.
source "$(dirname "$0")/common.sh"
cd "$ROOT"
[ "$CAMPUS_ENV" = dev ] || { echo ".env es de $CAMPUS_ENV: en el servidor se usa git pull y make deploy." >&2; exit 1; }

git pull --rebase --autostash || echo "Aviso: no se pudo hacer git pull; sigo con lo que hay local." >&2
git submodule update --init --recursive 2>/dev/null || true

"$VENV/bin/pip" install -r requirements.txt
# Primero los plugins: sus valores por omisión (CAMPUS_WEB_URL...) los usa la configuración.
apply_plugins
apply_config
apply_mounts
# Con 8 GB de RAM la construcción se queda sin memoria si la plataforma está encendida.
"$TUTOR" dev stop
"$TUTOR" images build openedx-dev
"$TUTOR" dev dc build campus-cms
build_mfe_if_changed

"$TUTOR" dev start -d
"$TUTOR" dev do init
"$TUTOR" dev restart
echo "Actualizado."
