#!/usr/bin/env bash
# Respaldo de usuarios, cursos y progreso (MySQL + MongoDB), del CMS (cursos a la venta, precios,
# ventas e imágenes) y de los videos subidos desde Campus en backups/<ambiente>-AAAA-MM-DD_HHMM/.
source "$(dirname "$0")/common.sh"
cd "$ROOT"
OUT="backups/$CAMPUS_ENV-$(date +%Y-%m-%d_%H%M)"
mkdir -p "$OUT"
"$TUTOR" "$MODE" start -d mysql mongodb
DBS=openedx
# Una instalación sin el CMS (por ejemplo, la vieja de TUTOR_ROOT_OVERRIDE) no tiene su base.
CMS_DB="$("$TUTOR" config printvalue CAMPUS_CMS_MYSQL_DATABASE 2>/dev/null || true)"
if [ -n "$CMS_DB" ] && "$TUTOR" "$MODE" dc exec -T mysql sh -c "mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" -e 'USE $CMS_DB'" 2>/dev/null; then
  DBS="$DBS $CMS_DB"
fi
"$TUTOR" "$MODE" dc exec -T mysql sh -c "mysqldump -uroot -p\"\$MYSQL_ROOT_PASSWORD\" --databases $DBS" > "$OUT/mysql.sql"
"$TUTOR" "$MODE" dc exec -T mongodb mongodump --db openedx --archive > "$OUT/mongodb.archive"
# Videos subidos desde /admin de Campus e imágenes de los cursos del CMS: viven en disco, no en Open edX.
VIDEOS="$(videos_dir)"
[ -d "$VIDEOS" ] && tar -czf "$OUT/videos.tar.gz" -C "$VIDEOS" .
MEDIA="$(cms_media_dir)"
[ -d "$MEDIA" ] && tar -czf "$OUT/cms-media.tar.gz" -C "$MEDIA" .
echo "Respaldo en $OUT"
