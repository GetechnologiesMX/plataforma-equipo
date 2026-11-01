#!/usr/bin/env bash
# Restaura un respaldo: make restore BACKUP=backups/dev-2026-10-13_1500 (backups/qa-... en el servidor)
source "$(dirname "$0")/common.sh"
cd "$ROOT"
DIR="${1:?Indica la carpeta: make restore BACKUP=backups/...}"
read -r -p "Esto reemplaza los datos de $CAMPUS_ENV en esta máquina con $DIR. ¿Continuar? [s/N] " ok
[ "$ok" = "s" ] || { echo "Cancelado."; exit 1; }
CMS_DB="$("$TUTOR" config printvalue CAMPUS_CMS_MYSQL_DATABASE)"
DBS=openedx
# Los respaldos anteriores al CMS no traen su base: en ese caso se deja la actual.
grep -q "^CREATE DATABASE .*\`$CMS_DB\`" "$DIR/mysql.sql" && DBS="$DBS $CMS_DB"
"$TUTOR" "$MODE" start -d mysql mongodb
# Se borran las bases completas para que no queden tablas que el respaldo no conoce;
# después `do init` vuelve a crear las de los plugins nuevos.
for db in $DBS; do
  "$TUTOR" "$MODE" dc exec -T mysql sh -c "mysql -uroot -p\"\$MYSQL_ROOT_PASSWORD\" -e 'DROP DATABASE IF EXISTS $db'"
done
"$TUTOR" "$MODE" dc exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD"' < "$DIR/mysql.sql"
"$TUTOR" "$MODE" dc exec -T mongodb mongorestore --drop --archive < "$DIR/mongodb.archive"
if [ -f "$DIR/videos.tar.gz" ]; then
  mkdir -p "$(videos_dir)"
  tar -xzf "$DIR/videos.tar.gz" -C "$(videos_dir)"
fi
if [ -f "$DIR/cms-media.tar.gz" ]; then
  mkdir -p "$(cms_media_dir)"
  tar -xzf "$DIR/cms-media.tar.gz" -C "$(cms_media_dir)"
fi
"$TUTOR" "$MODE" do init
"$TUTOR" "$MODE" restart
echo "Restaurado."
