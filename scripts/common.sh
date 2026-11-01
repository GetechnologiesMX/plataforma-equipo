#!/usr/bin/env bash
# Variables comunes: cada repo tiene su propio Tutor, así dos proyectos nunca se mezclan.
#
# Todo se lee de .env, copia de la plantilla del ambiente con las llaves llenas:
#   cp .env.dev .env    tutor dev en tu máquina
#   cp .env.qa .env     tutor local en el VPS de pruebas
#   cp .env.prod .env   tutor local en el servidor de producción
# CAMPUS_ENV (dentro de .env) dice cuál es. Lo compartido por todos está en config/tutor.env.
# dev guarda su Tutor en .tutor-dev/ y qa o prod en .tutor/ (make build usa una carpeta temporal).
set -eo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Lee un archivo CLAVE=valor ignorando comentarios y líneas vacías.
# También quita los comentarios al final de la línea (un # precedido de espacio), como en el README.
read_kv() {
  [ -f "$1" ] || return 0
  grep -vE '^[[:space:]]*(#|$)' "$1" | sed -E 's/[[:space:]]+#.*$//; s/[[:space:]]*$//' || true
}

ENV_FILE="$ROOT/.env"
# Un .env anterior a los ambientes no trae CAMPUS_ENV: es de dev.
CAMPUS_ENV="$(read_kv "$ENV_FILE" | sed -n 's/^CAMPUS_ENV=//p' | tail -1)"
CAMPUS_ENV="${CAMPUS_ENV:-dev}"
case "$CAMPUS_ENV" in
  dev)     MODE=dev ;;
  qa|prod) MODE=local ;;
  *) echo "CAMPUS_ENV=$CAMPUS_ENV en $ENV_FILE no existe (usa dev, qa o prod)" >&2; exit 1 ;;
esac
if [ "$MODE" = dev ]; then TUTOR_DIR=.tutor-dev; else TUTOR_DIR=.tutor; fi
# TUTOR_ROOT_OVERRIDE permite apuntar a otra instalación (por ejemplo, para respaldar la anterior).
export TUTOR_ROOT="${TUTOR_ROOT_OVERRIDE:-$ROOT/$TUTOR_DIR}"
export TUTOR_PLUGINS_ROOT="$ROOT/tutor-plugins"
VENV="$ROOT/venv"
TUTOR="$VENV/bin/tutor"
# Qué ambiente tiene esta carpeta de Tutor (lo escribe apply_config). Un .tutor/ sin archivo es
# una instalación de dev anterior a .tutor-dev/.
ENV_MARKER="$TUTOR_ROOT/campus-env"

# Antes dev también usaba .tutor/: la primera vez que corre cualquier comando de dev, se mueve
# a .tutor-dev/ (con usuarios, cursos y todo). Los contenedores se recrean con la ruta nueva.
if [ "$MODE" = dev ] && [ -z "${TUTOR_ROOT_OVERRIDE:-}" ] && [ ! -e "$ROOT/.tutor-dev" ] \
  && [ -f "$ROOT/.tutor/config.yml" ] && [ "$(cat "$ROOT/.tutor/campus-env" 2>/dev/null || echo dev)" = dev ]; then
  echo "Moviendo tu instalación de dev de .tutor/ a .tutor-dev/ (solo esta vez)..." >&2
  if [ -x "$TUTOR" ]; then TUTOR_ROOT="$ROOT/.tutor" "$TUTOR" dev dc down --remove-orphans >&2 || true; fi
  mv "$ROOT/.tutor" "$ROOT/.tutor-dev"
  echo dev > "$ENV_MARKER"
  if [ -x "$TUTOR" ]; then "$TUTOR" config save >/dev/null; fi
  echo "Listo. Enciende con make start si estaba encendida." >&2
fi

if [ -f "$TUTOR_ROOT/config.yml" ]; then
  installed="$(cat "$ENV_MARKER" 2>/dev/null || echo dev)"
  if [ "$installed" != "$CAMPUS_ENV" ]; then
    echo "$TUTOR_DIR/ es del ambiente $installed, pero .env dice $CAMPUS_ENV." >&2
    echo "Copia la plantilla de esta máquina (cp .env.$installed .env) y pon sus llaves." >&2
    exit 1
  fi
fi

read_list() {
  [ -f "$1" ] || return 0
  grep -vE '^[[:space:]]*(#|$)' "$1" | sed 's/[[:space:]]*$//' || true
}

# Toda la configuración del ambiente: lo compartido, las imágenes de los servidores (solo qa y prod)
# y después .env (que gana).
env_kv() {
  read_kv "$ROOT/config/tutor.env"
  if [ "$MODE" = local ]; then read_kv "$ROOT/config/images.env"; fi
  read_kv "$ENV_FILE"
}

apply_config() {
  local args=() lines=() keys=" " line name val
  # NUXT_* (variables de Campus) no son configuración de Tutor. CAMPUS_ENV sí se guarda: lo usa
  # el nombre de la imagen de los MFE (config/images.env).
  # Tutor resuelve cada {{ CLAVE }} al guardarla: una vez por clave (gana el último archivo),
  # primero los valores fijos y después los que usan otras claves.
  while IFS= read -r line; do lines+=("$line"); keys+="${line%%=*} "; done < <(env_kv | grep -vE '^NUXT_' | awk '
    { key = substr($0, 1, index($0, "=") - 1); if (!(key in value)) order[n++] = key; value[key] = $0 }
    END {
      for (i = 0; i < n; i++) if (index(value[order[i]], "{{") == 0) print value[order[i]]
      for (i = 0; i < n; i++) if (index(value[order[i]], "{{") > 0) print value[order[i]]
    }' || true)
  for line in ${lines[@]+"${lines[@]}"}; do
    # Al guardar, Tutor solo conoce lo que ya está en config.yml, no los valores por omisión de los
    # plugins (por ejemplo CAMPUS_WEB_URL de campusweb si .env no lo trae): esos se ponen aquí.
    for name in $(grep -oE '\{\{ *[A-Z0-9_]+ *\}\}' <<<"$line" | tr -d '{} ' | sort -u); do
      case "$keys" in *" $name "*) continue ;; esac
      val="$("$TUTOR" config printvalue "$name")"
      line="${line//"{{ $name }}"/"$val"}"
      line="${line//"{{$name}}"/"$val"}"
    done
    args+=(--set "$line")
  done
  "$TUTOR" config save ${args[@]+"${args[@]}"}
  echo "$CAMPUS_ENV" > "$ENV_MARKER"
}

# Crea el venv con el Tutor de requirements.txt (o lo reutiliza si ya está con el mismo Python).
ensure_venv() {
  # En macOS `python3` suele ser el 3.9 de Apple: se prefiere un Python más nuevo si existe.
  local python="${PYTHON:-}"
  if [ -z "$python" ]; then
    for p in python3.13 python3.12 python3.11 python3.10 python3; do
      if command -v "$p" >/dev/null; then python="$p"; break; fi
    done
  fi
  # Si el venv se creó con otro Python (o quedó a medias sin bin/tutor), se crea de nuevo.
  if [ -x "$VENV/bin/python" ] && [ -x "$VENV/bin/tutor" ] \
    && [ "$("$VENV/bin/python" -c 'import sys; print(sys.version_info[:2])')" = "$("$python" -c 'import sys; print(sys.version_info[:2])')" ]; then
    :
  else
    rm -rf "$VENV"
    "$python" -m venv "$VENV"
  fi
  "$VENV/bin/pip" install --upgrade pip
  "$VENV/bin/pip" install -r "$ROOT/requirements.txt"
}

apply_plugins() {
  # Deja activos exactamente los plugins de config/plugins.txt más los de tutor-plugins/.
  local wanted=()
  while IFS= read -r p; do wanted+=("$p"); done < <(read_list "$ROOT/config/plugins.txt")
  for f in "$TUTOR_PLUGINS_ROOT"/*.py "$TUTOR_PLUGINS_ROOT"/*.yml; do
    [ -e "$f" ] || continue
    wanted+=("$(basename "${f%.*}")")
  done
  local enabled
  enabled="$("$TUTOR" plugins list | awk '/enabled/ {print $1}')"
  for p in $enabled; do
    if ! printf '%s\n' "${wanted[@]}" | grep -qx "$p"; then
      "$TUTOR" plugins disable "$p"
    fi
  done
  [ ${#wanted[@]} -eq 0 ] || "$TUTOR" plugins enable "${wanted[@]}"
}

apply_mounts() {
  # Reemplaza la lista completa de montajes por la de config/mounts.txt.
  local items=()
  while IFS= read -r m; do
    if [ -d "$ROOT/$m" ]; then
      items+=("\"$ROOT/$m\"")
    else
      echo "Aviso: no existe $m (¿falta clonarlo?). Se omite." >&2
    fi
  done < <(read_list "$ROOT/config/mounts.txt")
  local joined
  joined="$(IFS=,; echo "${items[*]:-}")"
  "$TUTOR" config save --set "MOUNTS=[$joined]"
}

# Reconstruye la imagen de los MFE (menú, logo y header de Campus) solo si cambió lo que Tutor
# genera para construirla (tutor-plugins/campusmenu.py, el dominio de Campus, la versión de Tutor).
# Tarda varios minutos; si no cambió nada, no hace nada.
build_mfe_if_changed() {
  local dir="$TUTOR_ROOT/env/plugins/mfe/build" hash_file="$TUTOR_ROOT/.mfe-build-hash" hash
  [ -d "$dir" ] || "$TUTOR" config save >/dev/null
  # shasum viene en macOS y en Linux; sha256sum solo en Linux.
  hash="$(cd "$dir" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -d' ' -f1)"
  if [ "$hash" != "$(cat "$hash_file" 2>/dev/null)" ]; then
    echo "Cambió la configuración de los MFEs: reconstruyendo (tarda varios minutos)..."
    "$TUTOR" images build mfe
    echo "$hash" > "$hash_file"
  fi
}

# Las imágenes propias de qa y prod: Open edX (con el plugin del LMS), los MFE (con el menú de
# Campus), el CMS y Campus. Se construyen en tu máquina y el servidor las baja del registro.
SERVER_IMAGES=(openedx mfe campus-cms campus-web)
# La clave de Tutor con el nombre completo (registro y etiqueta) de cada una (config/images.env).
image_key() {
  case "$1" in
    openedx) echo DOCKER_IMAGE_OPENEDX ;;
    mfe) echo MFE_DOCKER_IMAGE ;;
    campus-cms) echo CAMPUS_CMS_DOCKER_IMAGE ;;
    campus-web) echo CAMPUS_WEB_DOCKER_IMAGE ;;
  esac
}

# Dónde quedan en disco los videos de Campus y las imágenes del CMS.
videos_dir() {
  if [ "$MODE" = dev ]; then echo "$ROOT/src/front-campus/.data/videos"; else echo "$TUTOR_ROOT/data/campus-web/videos"; fi
}
cms_media_dir() {
  if [ "$MODE" = dev ]; then echo "$ROOT/src/campus-cms/media"; else echo "$TUTOR_ROOT/data/campus-cms/media"; fi
}
