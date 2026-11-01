#!/usr/bin/env bash
# Aplica config/tutor.env y .env sin reconstruir nada
# (por ejemplo, después de cambiar una llave).
source "$(dirname "$0")/common.sh"
cd "$ROOT"
apply_config
if [ "$MODE" = dev ]; then
  "$TUTOR" dev restart lms
  # El CMS recibe su configuración como variables del contenedor: hay que recrearlo.
  "$TUTOR" dev start -d campus-cms
else
  # Recrea los contenedores cuya configuración cambió (CMS, Campus, Caddy) y reinicia
  # los que leen archivos de configuración montados.
  "$TUTOR" local start -d
  "$TUTOR" local restart lms cms lms-worker cms-worker caddy
fi
