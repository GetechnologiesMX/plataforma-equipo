#!/usr/bin/env bash
# Levanta el sitio público (Nuxt) en http://www.local.openedx.io:3000
source "$(dirname "$0")/common.sh"
cd "$ROOT"
DIR="${FRONT_DIR:-src/front-campus}"
[ -d "$DIR" ] || { echo "No existe $DIR (¿falta git submodule update --init?)" >&2; exit 1; }
command -v node >/dev/null || { echo "Instala Node 22.5 o más nuevo (por ejemplo con nvm)." >&2; exit 1; }
node -e 'const [a,b]=process.versions.node.split(".").map(Number); process.exit(a>22||(a===22&&b>=5)?0:1)' \
  || { echo "Necesitas Node 22.5 o más nuevo; tienes $(node -v)." >&2; exit 1; }
# Las NUXT_* de .env cambian las direcciones de nuxt.config.ts.
while IFS= read -r line; do export "$line"; done < <(env_kv | grep -E '^NUXT_' || true)
cd "$DIR"
[ -d node_modules ] && [ node_modules -nt package-lock.json ] || npm ci
echo "Sitio público en http://www.local.openedx.io:3000"
exec npm run dev -- --host 0.0.0.0
