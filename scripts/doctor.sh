#!/usr/bin/env bash
# Muestra el estado para comparar entre máquinas del equipo.
source "$(dirname "$0")/common.sh"
cd "$ROOT"
echo "== Repo";      git log -1 --oneline 2>/dev/null || echo "(sin git)"
echo "== Ambiente";  echo "$CAMPUS_ENV (tutor $MODE)"
echo "== Tutor";     "$TUTOR" --version
echo "== Raíz";      echo "$TUTOR_ROOT"
echo "== Plugins";   "$TUTOR" plugins list | grep -E 'enabled' || true
echo "== Montajes";  "$TUTOR" mounts list
echo "== Docker";    docker system df
if [ "$MODE" = dev ]; then
  CMS_HEALTH="http://campus-cms.local.openedx.io:8010/api/health/"
else
  CMS_HEALTH="https://$("$TUTOR" config printvalue CAMPUS_CMS_HOST)/api/health/"
fi
echo "== CMS";       curl -fsS --max-time 5 "$CMS_HEALTH" && echo \
                   || echo "No responde (¿make start? revisa make cms-logs)"
