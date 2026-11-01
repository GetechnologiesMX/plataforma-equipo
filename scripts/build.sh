#!/usr/bin/env bash
# Construye y sube al registro las imágenes del ambiente de .env (CAMPUS_ENV=qa o prod) cuya
# versión de config/images.env todavía no está publicada. Antes: docker login <registro>.
# En tu máquina: cp .env.qa .env (o .env.prod), make build, y regresa tu .env de dev.
# Usa un Tutor temporal, así que no toca .tutor-dev/ ni .tutor/.
TUTOR_ROOT_OVERRIDE="$(mktemp -d)"
trap 'rm -rf "$TUTOR_ROOT_OVERRIDE"' EXIT
source "$(dirname "$0")/common.sh"
cd "$ROOT"
[ "$MODE" = local ] || { echo "make build es para qa o prod: copia a .env su plantilla (cp .env.qa .env)" >&2; exit 1; }

git submodule update --init --recursive
[ -x "$TUTOR" ] || ensure_venv
# Las llaves no entran en las imágenes: Tutor solo las escribe en la configuración que se monta
# al encender. Por eso aquí basta la plantilla, aunque tenga las llaves en ...
# Primero los plugins: sus valores por omisión (CAMPUS_WEB_URL...) los usa la configuración.
apply_plugins
apply_config
# El plugin del LMS se instala dentro de la imagen de Open edX (Tutor lo toma de los montajes al construir).
apply_mounts

# Solo las imágenes cuya etiqueta no está en el registro.
todo=()
for image in "${SERVER_IMAGES[@]}"; do
  name="$("$TUTOR" config printvalue "$(image_key "$image")")"
  if docker manifest inspect "$name" >/dev/null 2>&1; then
    echo "Ya publicada, se omite: $name"
  else
    todo+=("$image")
  fi
done
if [ ${#todo[@]} -eq 0 ]; then
  echo "Nada que construir: todas las versiones de config/images.env ya están en el registro."
  exit 0
fi

# El CMS y Campus se construyen desde sus submódulos: avisa si llevan cambios sin commit.
for image in "${todo[@]}"; do
  case "$image" in campus-cms) dir=src/campus-cms ;; campus-web) dir=src/front-campus ;; *) continue ;; esac
  [ -z "$(git -C "$dir" status --porcelain)" ] \
    || echo "Aviso: $dir tiene cambios sin commit; entran en la imagen de $image." >&2
done

"$TUTOR" images build "${todo[@]}"
"$TUTOR" images push "${todo[@]}"
echo
echo "Publicadas para $CAMPUS_ENV:"
for image in "${todo[@]}"; do
  echo "  $("$TUTOR" config printvalue "$(image_key "$image")")"
done
echo "Haz commit de config/images.env y, en el servidor: make deploy"
