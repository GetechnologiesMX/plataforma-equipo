# Plataforma del equipo (Open edX + Tutor)

Este repo define toda la plataforma: la versión de Tutor, los plugins, la configuración y el código propio. Clonas, corres `make setup` y tu máquina queda igual que la de los demás.

| Carpeta | Qué es | Repo |
| --- | --- | --- |
| `src/openedx-course-payments` | Plugin del LMS: solo entran quienes pagaron y las páginas de curso van a Campus (Django) | `openedx-course-payments` (submódulo) |
| `src/front-campus` | Sitio público Campus (Nuxt) | `front-campus` (submódulo) |
| `src/campus-cms` | CMS del contador: cursos, precios y ventas; cobra con Stripe (Django + DRF) | `campus-cms` (submódulo) |
| `tutor-plugins/` | Plugins de Tutor del equipo (el CMS, el plugin del LMS y el menú de Campus en Open edX) | este repo |
| `config/` | Plugins activos, montajes y `tutor.env` (lo que comparten todos los ambientes: nombre, idioma, colores) | este repo |
| `.env.dev` / `.env.qa` / `.env.prod` | Plantilla de cada ambiente: direcciones, imágenes, correo y las llaves vacías | este repo |
| `.env` | La configuración que usan todos los comandos: copia de una plantilla con las llaves llenas. **Nunca se sube a Git** | solo en cada máquina |
| `src/frontend-app-*` | Copias locales de MFEs de Open edX para probar cambios (ignoradas por Git) | solo en tu máquina |

Hay tres ambientes: **dev** (`tutor dev` en la máquina de cada quien, lo de las secciones 1 a 10), **qa** y **prod** (`tutor local` en un servidor, con HTTPS y las imágenes del registro del equipo, sección 11). El ambiente de cada máquina lo decide qué plantilla copiaste a `.env` (`CAMPUS_ENV`). Los mismos comandos (`make logs`, `make backup`...) sirven en los tres.

Direcciones en dev:

- LMS: http://local.openedx.io:8000
- Studio: http://studio.local.openedx.io:8001
- Campus: http://www.local.openedx.io:3000
- CMS (API): http://campus-cms.local.openedx.io:8010/api/health/

## Ramas

Los cuatro repos (este y los tres submódulos) trabajan igual:

| Rama | Para qué |
| --- | --- |
| `dev` | Integración: aquí llega todo lo terminado. Es la rama con la que se trabaja a diario. |
| `main` | Estable: solo recibe `dev` cuando todo funciona junto. |
| `feat/...`, `fix/...` | Tu trabajo en curso; sale de `dev` y vuelve a `dev` con un pull request. |

En `dev`, este repo apunta al `dev` de cada submódulo, y `.gitmodules` les pone `branch = dev` (así `git submodule update --remote` trae lo último de `dev`). Detalles en la sección 5.

## Cómo funciona

| Quién | Dónde | Qué hace |
| --- | --- | --- |
| Contador | Campus → `/admin` | Crea el curso o toma uno que ya existe en Open edX (el CMS lo da de alta con sus autores), le pone precio e imagen, lo pone a la venta y ve las ventas |
| Autor | Campus → `/admin` → *Contenido*, o Studio | Arma el temario: módulos, lecciones, videos y evaluaciones (tiene rol de instructor en el curso) |
| Comprador | Campus | Compra con Stripe; el CMS recibe el pago y lo inscribe en Open edX |
| Alumno | Open edX (MFE de aprendizaje) | Toma el curso; solo entra si lo pagó |

- **El CMS (`campus-cms`) es la fuente de verdad de lo comercial:** qué cursos se venden, precios, imágenes, descripciones, órdenes y pagos. **Open edX** lo es del contenido, los usuarios, las inscripciones y el progreso. Se enlazan por la clave del curso (`course-v1:Campus+CODIGO+PERIODO`).
- **Un curso creado directo en Studio no aparece en Campus ni se puede vender** hasta que lo tomas en `/admin/cursos/nuevo` → *Tomar un curso de Open edX* (debe ser de la organización del CMS, `Campus`).
- **El contenido vive en Open edX** aunque se edite desde Campus: la pestaña *Contenido* llama a Studio con tu usuario, así que solo puedes editar los cursos donde eres autor (o si eres staff). Los videos que subes se guardan en el disco de Campus (`src/front-campus/.data/videos`).
- **El plugin del LMS (`openedx-course-payments`)** solo deja entrar a quien pagó (o al equipo del curso) y manda las páginas "About" del LMS a Campus.
- **Quién es contador** lo decide el CMS, no Open edX. Ser staff de Open edX no da acceso a `/admin`; el rol se da con `make tutor ARGS="dev exec campus-cms python manage.py contador <usuario>"`.

Cada submódulo tiene su README con el detalle: `src/campus-cms/README.md`, `src/front-campus/README.md`, `src/openedx-course-payments/README.md`.

---

## 1. Primera vez (solo una vez por máquina)

### 1.1 Instala lo necesario

| Sistema | Qué instalar |
| --- | --- |
| Windows | WSL2 con Ubuntu y Docker Desktop con la integración WSL activa. Todo se hace **dentro de Ubuntu** (`~/...`), nunca en `/mnt/c`. |
| macOS | Docker Desktop, `xcode-select --install` y `brew install python` |
| Linux | Docker Engine |

En Ubuntu (o Linux):

```bash
sudo apt update
sudo apt install -y git make python3 python3-venv python3-pip curl unzip
```

Node 22.5 o más nuevo (para Campus):

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 22
```

Stripe CLI (para recibir los pagos de prueba): https://docs.stripe.com/stripe-cli

**Memoria en Windows:** crea `C:\Users\<tu usuario>\.wslconfig` con esto y luego corre `wsl --shutdown` en PowerShell:

```ini
[wsl2]
memory=10GB
swap=8GB
```

### 1.2 Clona el repo con sus submódulos

```bash
git clone --recurse-submodules --branch dev https://github.com/TU_ORG/plataforma-equipo.git ~/plataforma-equipo
cd ~/plataforma-equipo
```

Revisa que las tres carpetas tengan archivos: `ls src/openedx-course-payments src/front-campus src/campus-cms`. Si salen vacías, corre `git submodule update --init --recursive`.

### 1.3 Pon tus llaves

Crea tu `.env` desde la plantilla de dev y pon tu llave de Stripe en `CAMPUS_CMS_STRIPE_SECRET_KEY` (solo llaves de prueba, `sk_test_`, nunca `sk_live_`). El `whsec_` lo obtienes en el paso 1.6.

```bash
cp .env.dev .env
nano .env
```

Si ya tenías un `.env` con solo las llaves, cópialas a una copia nueva de `.env.dev` y usa esa como `.env`.

### 1.4 Instala la plataforma

Abre Docker Desktop y espera a que diga *Running*. Luego:

```bash
make setup
make admin USER_NAME=admin EMAIL=tu@correo.com
make contador USER_NAME=admin
```

`make setup` tarda bastante la primera vez porque descarga y construye las imágenes (también la del CMS) y prepara la base de datos y la cuenta de servicio del CMS. `make admin` te pide la contraseña del administrador.

Para usar la administración de Campus, dale el rol de contador a tu usuario (puede ser el mismo `admin`):

```bash
make tutor ARGS="dev exec campus-cms python manage.py contador admin"
```

El menú de Campus en los encabezados de Open edX (`tutor-plugins/campusmenu.py`) se compila dentro de la imagen de los MFE. La primera vez, y cada vez que cambie ese archivo:

```bash
make tutor ARGS="images build mfe"
make tutor ARGS="dev start -d mfe"
```

Usa `dev start -d mfe`, no `dev restart mfe`: `restart` reinicia el mismo contenedor con la imagen vieja, y `start` lo recrea con la nueva.

### 1.5 Levanta Campus (en otra terminal)

```bash
cd ~/plataforma-equipo
make front
```

### 1.6 Conecta Stripe (en una tercera terminal)

```bash
cd ~/plataforma-equipo
make stripe
```

Copia el `whsec_...` que aparece, pégalo en `CAMPUS_CMS_STRIPE_WEBHOOK_SECRET` dentro de `.env` y corre `make config`. Solo se repite si el `whsec_` cambia. Los pagos los recibe el CMS (`campus-cms`).

Listo: abre http://www.local.openedx.io:3000. Para vender un curso entra a http://www.local.openedx.io:3000/admin con tu usuario contador: crea el curso, ponle precio e imagen, créalo en Open edX y ponlo a la venta. Aparece en el catálogo y se compra con la tarjeta de prueba `4242 4242 4242 4242`.

### 1.7 Ya tenía la plataforma instalada antes del CMS

Corre `make update` (construye el CMS, crea su base y su cuenta de servicio). En tu `.env`, las llaves de Stripe ahora se llaman `CAMPUS_CMS_STRIPE_SECRET_KEY` y `CAMPUS_CMS_STRIPE_WEBHOOK_SECRET` (antes `COURSE_PAYMENTS_STRIPE_...`): cámbiales el nombre, corre `make config` y luego `make contador USER_NAME=<tu usuario>`.

---

## 2. Cada vez que vas a trabajar

1. Abre Docker Desktop y espera a *Running*.
2. Enciende la plataforma:

   ```bash
   cd ~/plataforma-equipo
   make update   # solo si el equipo subió cambios (sección 3)
   make start
   ```

3. En otra terminal: `make front`.
4. Si vas a probar pagos, en otra terminal: `make stripe`.

Al terminar: `Ctrl+C` en las terminales de `make front` y `make stripe`, y luego `make stop`.

---

## 3. El equipo subió cambios: ¿qué corro?

| Qué cambió | Qué corres |
| --- | --- |
| Cualquier cosa de `plataforma-equipo` (config, plugins, versión de Tutor, scripts) | `make update` |
| El plugin del LMS (`openedx-course-payments`) o el CMS (`campus-cms`), ya registrados en `plataforma-equipo` | `make update` |
| Solo Campus (`front-campus`), ya registrado en `plataforma-equipo` | `git pull && git submodule update --init --recursive`, y reinicia `make front` |
| Alguien subió directo a un submódulo (`front-campus`, `campus-cms` o el plugin) | Ver la sección siguiente: `make update` no lo trae solo |
| `tutor-plugins/campusmenu.py` (el menú en Open edX) | `make update` y luego `make tutor ARGS="images build mfe"` y `make tutor ARGS="dev start -d mfe"` |
| No sé qué cambió | `make update` (siempre es seguro, solo tarda más) |

`make update` hace todo en orden: `git pull`, actualiza los submódulos, aplica configuración y plugins, reconstruye las imágenes de Open edX y del CMS, corre las migraciones e inicializa lo que falte (base de datos y cuenta de servicio del CMS), y reinicia. Apaga la plataforma mientras construye, así que tarda unos minutos. No reconstruye la imagen de los MFE (el menú): eso va aparte, ver la tabla.

**Antes de `make update`**, sube lo que tengas a medias dentro de `src/`: actualizar los submódulos los regresa al commit que marca este repo.

### Alguien subió cambios directo a un submódulo (`front-campus`, `campus-cms` o el plugin)

**`make update` NO trae esos cambios por sí solo.** Este repo guarda en qué commit está cada submódulo, y `make update` deja cada uno en ese commit guardado. Si alguien abre solo el repo `front-campus`, `campus-cms` u `openedx-course-payments` y hace push ahí, `plataforma-equipo` sigue apuntando al commit anterior.

Los tres submódulos siguen la rama `dev` de su repo (`branch = dev` en `.gitmodules`).
**`make update` NO trae esos cambios por sí solo.** Este repo guarda en qué commit está cada submódulo, y `make update` deja cada uno en ese commit guardado. Si alguien hace push solo en el repo de `front-campus`, `campus-cms` u `openedx-course-payments`, `plataforma-equipo` sigue apuntando al commit anterior.

Para que el equipo reciba el cambio, **quien lo subió** (o cualquiera) actualiza el commit guardado en `plataforma-equipo`:

```bash
cd ~/plataforma-equipo
git checkout dev && git pull
git submodule update --remote src/front-campus   # o src/campus-cms, src/openedx-course-payments: trae lo último de su rama dev
git add src/front-campus
git commit -m "Actualiza front-campus"
git push
```

Después de ese push, los demás ya lo reciben con `make update`.

Para probar en tu máquina lo último de un submódulo sin subir nada: `git submodule update --remote` y luego, según qué cambió, `make restart`, reinicia `make front` o `make update`. El siguiente `make update` lo regresa al commit guardado mientras nadie actualice `plataforma-equipo`.

---

## 4. Modifiqué algo con todo encendido: ¿hay que reiniciar?

Con la plataforma encendida (`make start`) y Campus corriendo (`make front`):

| Modifiqué | Qué hago |
| --- | --- |
| Páginas, componentes o estilos de Campus | Nada, el navegador se actualiza solo |
| `nuxt.config.ts` o variables de entorno de Campus | `Ctrl+C` y `make front` |
| `package.json` de Campus (nueva dependencia) | `Ctrl+C` y `make front` (instala solo) |
| Código Python del plugin del LMS | Nada, el LMS se recarga solo en unos segundos. Si no ves el cambio: `make restart` |
| Modelos del plugin (hay una migración nueva) | `make tutor ARGS="dev exec lms ./manage.py lms migrate"` |
| Dependencias del plugin (`setup.py` o `pyproject.toml`) | `make update` |
| El archivo de Tutor del plugin (`tutor/coursepayments.py`) | `make config` y luego `make restart` |
| El menú de Campus en Open edX (`tutor-plugins/campusmenu.py`) | `make tutor ARGS="images build mfe"` y `make tutor ARGS="dev start -d mfe"` |
| Código Python del CMS (`campus-cms`) | Nada, se recarga solo |
| Modelos del CMS (hay una migración nueva) | `make tutor ARGS="dev exec campus-cms python manage.py migrate"` |
| Dependencias del CMS (`requirements.txt` o `Dockerfile` de `campus-cms`) | `make update` |
| El archivo de Tutor del CMS (`tutor/campuscms.py`) | `make config`; si agrega tareas de inicio (`CLI_DO_INIT_TASKS`), `make update` |
| `config/tutor.env` o `.env` | `make config` |
| `config/plugins.txt`, `config/mounts.txt`, `tutor-plugins/` o `requirements.txt` | `make update` |

Regla corta: el **código** se recarga solo, la **configuración** es `make config`, y los **plugins o dependencias** son `make update`.

---

## 5. Trabajar dentro de un submódulo

Después de clonar, los submódulos quedan sin rama (en el commit que guarda este repo). Antes de editar, sal de `dev` en una rama tuya:

```bash
cd ~/plataforma-equipo/src/campus-cms   # o src/front-campus, src/openedx-course-payments
git checkout dev
git pull
git checkout -b feat/mi-cambio
# ... editas y pruebas ...
git add -A && git commit -m "Describe el cambio"
git push -u origin feat/mi-cambio
```

Abre un pull request de `feat/mi-cambio` hacia `dev`. Cuando se fusione, actualiza el commit del submódulo en `dev` de este repo (sección 3) para que el equipo lo reciba.

Lo mismo para este repo: rama desde `dev`, pull request hacia `dev`. `main` solo recibe `dev` cuando todo funciona junto.

---

## 6. Agregar o quitar plugins

Todo cambio de plugins es un commit en este repo seguido de `make update`. Al hacer `git push`, los demás lo reciben con su propio `make update`.

### Plugin de la comunidad (por ejemplo `notes` o `forum`)

1. Si no viene incluido en `tutor[full]`, agrega su paquete a `requirements.txt` (por ejemplo `tutor-xyz==21.0.*`).
2. Agrega su nombre en una línea de `config/plugins.txt`.
3. `make update`.

### Plugin propio de Tutor

1. Pon el archivo `.py` o `.yml` en `tutor-plugins/`, o un enlace al que viene dentro de un submódulo:

   ```bash
   ln -s ../src/openedx-course-payments/tutor/coursepayments.py tutor-plugins/coursepayments.py
   ```

2. `make update`. Todo lo que está en `tutor-plugins/` se activa solo.

### Código propio que corre dentro de Open edX (app de Django)

Así se agregó `openedx-course-payments`; para otro son los mismos pasos. Conviene nombrar la carpeta con `openedx-` al inicio (por ejemplo `openedx-mi-plugin`), porque así te ahorras el paso 3.

1. **El código.** Agrega el repo como submódulo:

   ```bash
   git submodule add https://github.com/TU_ORG/openedx-mi-plugin.git src/openedx-mi-plugin
   ```

2. **El montaje.** Escribe a mano `src/openedx-mi-plugin` en una línea nueva de `config/mounts.txt` (no se agrega solo). Así Tutor pone esa carpeta dentro del LMS y tus cambios se ven sin reconstruir.

3. **Que Tutor la instale.** Montar la carpeta no basta: Tutor solo instala la carpeta como app de Django si su nombre está en su lista. Tutor 21 ya acepta solo los nombres que empiezan con `openedx-` (por eso `openedx-course-payments` funciona sin nada extra), los que empiezan con `platform-plugin-` y los que contienen `xblock`.

   - **Si tu carpeta se llama así** (por ejemplo `src/openedx-mi-plugin`), no haces nada en este paso.
   - **Si se llama de otra forma**, agrega esta línea a un plugin de Tutor en `tutor-plugins/` (puede ser un archivo nuevo, `tutor-plugins/miplugin.py`):

     ```python
     from tutor import hooks
     hooks.Filters.MOUNTED_DIRECTORIES.add_item(("openedx", "mi-plugin"))
     ```

   Si el plugin trae además su propio archivo de Tutor con ajustes (como `tutor/coursepayments.py` en `openedx-course-payments`), enlázalo en `tutor-plugins/` para que se active:

   ```bash
   ln -s ../src/openedx-mi-plugin/tutor/miplugin.py tutor-plugins/miplugin.py
   ```

4. **Aplica y comparte.** Corre `make update` (reconstruye la imagen con el plugin instalado) y sube todo:

   ```bash
   git add .gitmodules src/openedx-mi-plugin config/mounts.txt tutor-plugins/
   git commit -m "Agrega mi-plugin"
   git push
   ```

### Servicio propio en su propio contenedor (Django aparte, como `campus-cms`)

Así se agregó `campus-cms`. A diferencia del plugin del LMS, no se monta dentro de Open edX: es otro contenedor de `tutor dev` con su propia base en el MySQL de Tutor. Todo lo define el archivo de Tutor que vive en su repo (`tutor/campuscms.py`).

1. **El código.** Agrega el repo como submódulo y que siga la rama del equipo:

   ```bash
   git submodule add -b dev https://github.com/TU_ORG/mi-servicio.git src/mi-servicio
   ```

2. **El archivo de Tutor.** El repo trae un `Dockerfile` y un plugin de Tutor que define:
   - el contenedor en `local-docker-compose-dev-services` (con `build` apuntando al repo y el repo montado, así el código se recarga solo) y su copia para tareas en `dev-docker-compose-jobs-services`;
   - su configuración en `CONFIG_DEFAULTS` (y los secretos generados una vez por máquina en `CONFIG_UNIQUE`);
   - sus tareas de `tutor dev do init` en `CLI_DO_INIT_TASKS`: crear la base de MySQL, la cuenta de servicio en el LMS y correr `migrate`.

   Enlázalo en `tutor-plugins/` para que se active:

   ```bash
   ln -s ../src/mi-servicio/tutor/miservicio.py tutor-plugins/miservicio.py
   ```

   **No** va en `config/mounts.txt`: ese archivo es solo para código que corre dentro del LMS.

3. **Los scripts de este repo.** Si el servicio tiene que reconstruirse o recrearse, agrégalo como se hizo con `campus-cms`:
   - `scripts/update.sh`: `"$TUTOR" dev dc build mi-servicio` (instala sus dependencias nuevas);
   - `scripts/config.sh`: `"$TUTOR" dev start -d mi-servicio` (recibe la configuración como variables del contenedor, así que hay que recrearlo);
   - `scripts/backup.sh` y `scripts/restore.sh`: su base de MySQL;
   - `Makefile`: `restart` y, si sirve, atajos como `make cms-logs`.

   Lo que cambia por ambiente (direcciones, llaves) va en `.env.dev`, `.env.qa` y `.env.prod` (sin llaves de verdad) con el nombre de su configuración (`CAMPUS_CMS_STRIPE_SECRET_KEY`), y lo que es igual en todos en `config/tutor.env`.

4. **Aplica y comparte.** `make update` y sube todo:

   ```bash
   git add .gitmodules src/mi-servicio tutor-plugins/ scripts/ Makefile README.md
   git commit -m "Agrega mi-servicio"
   git push
   ```

### Quitar un plugin

1. Borra su línea de `config/plugins.txt`, su archivo de `tutor-plugins/` o su línea de `config/mounts.txt`.
2. `make update`. Se desactiva en todas las máquinas.

Si además era un submódulo que ya no se usa: `git rm src/mi-plugin` y commit.

---

## 7. El CMS y el área de administración

| Para qué | Comando |
| --- | --- |
| Dar o quitar el rol Contador (entra a `/admin` de Campus) | `make contador USER_NAME=usuario` / `make contador USER_NAME=usuario REMOVE=1` |
| Ver los errores del CMS | `make cms-logs` |
| Revisar la conexión del CMS con Open edX | `make tutor ARGS="dev exec campus-cms python manage.py check_openedx"` |
| Reintentar accesos que fallaron y cerrar pagos sin webhook | `make tutor ARGS="dev exec campus-cms python manage.py reconcile_orders"` (o el botón *Reintentar* en `/admin/ventas`) |
| Correr las pruebas del CMS | `make tutor ARGS="dev exec campus-cms python manage.py test"` |
| Admin de Django del CMS (para revisar datos) | `make tutor ARGS="dev exec campus-cms python manage.py createsuperuser"` y http://campus-cms.local.openedx.io:8010/admin/ |

Nadie tiene contraseña en el CMS: se entra con el usuario de Open edX. El usuario contador inicia sesión en el LMS y Campus llama al CMS con ese login. El rol se puede dar antes de que la persona entre por primera vez.

El CMS habla con Open edX con una cuenta de servicio (`campus_cms_worker`) que crea `make setup` / `make update`. Si la borras o cambias el `CAMPUS_CMS_OAUTH2_CLIENT_SECRET`, corre `make update` para volver a crearla.

### Crear un curso y armar su contenido

1. En `/admin/cursos/nuevo` elige **Crear un curso nuevo** (o **Tomar un curso de Open edX** para uno que ya existe en Studio; conserva su contenido y alumnos). Deja tu usuario en *Autores*: así Studio te deja editar el contenido. Al guardar, el curso se crea en Open edX (tarda unos segundos) y se abre su pestaña *Contenido*.
2. En la pestaña *Contenido* agrega **módulos** y, dentro, **lecciones**. En cada lección:
   - **Videos:** arrástralos (MP4, WebM u Ogg, hasta 2 GB) o pega un enlace de YouTube o de un archivo de video.
   - **Evaluaciones:** opción múltiple, casillas, lista desplegable, respuesta numérica y respuesta de texto se escriben ahí mismo (pregunta, respuestas, explicación, puntos, intentos y cuándo se muestra la respuesta). Arrastrar y soltar, respuesta abierta, expresión matemática, zona en imagen y evaluación con Python se agregan ahí y se configuran con *Editar en Studio*.
   - **Calificación:** elige si la lección cuenta para la nota (Tarea, Laboratorio, Examen parcial, Examen final; los tipos y pesos se definen en Studio → Calificación) y su fecha límite.
3. Pulsa **Publicar cambios** (arriba, junto al nombre del curso): hasta entonces los alumnos no ven lo nuevo.
4. En *Información* sube la portada y escribe la descripción; en *Precio y venta* ponle precio y pulsa **Poner a la venta**.

Los videos subidos solo se ven mientras `make front` está corriendo (los sirve Campus) y entran en `make backup`.

---

## 8. Todos los comandos

| Comando | Para qué |
| --- | --- |
| `make` | Ver esta lista |
| `make setup` | Instalar desde cero (primera vez) |
| `make update` | Traer y aplicar los cambios del equipo |
| `make start` / `make stop` | Encender / apagar la plataforma |
| `make restart` | Reiniciar LMS, Studio y el CMS |
| `make config` | Aplicar cambios de `config/tutor.env` o `.env` |
| `make front` | Levantar Campus |
| `make stripe` | Recibir en el CMS los webhooks de prueba de Stripe |
| `make logs` | Ver los errores del LMS (`Ctrl+C` para salir) |
| `make cms-logs` | Ver los errores del CMS (`Ctrl+C` para salir) |
| `make contador USER_NAME=...` | Dar el rol Contador (`REMOVE=1` para quitarlo) |
| `make shell` | Consola de Django del LMS |
| `make admin USER_NAME=... EMAIL=...` | Crear un superusuario |
| `make backup` / `make restore BACKUP=backups/...` | Respaldar / restaurar usuarios, cursos, el CMS (cursos a la venta y ventas) y los videos subidos |
| `make doctor` | Ver versiones y estado para comparar con otra máquina |
| `make tutor ARGS="..."` | Cualquier comando de Tutor de este proyecto |
| `make reconcile` | Reintentar accesos que fallaron y cerrar pagos sin webhook |
| `make web-logs` | Ver los logs de Campus en qa/prod |
| `make build` | [tu máquina, con `.env` de qa o prod] Construir las imágenes y subirlas al registro |
| `make deploy` | [servidor] Bajar código e imágenes y encender o actualizar todo |

En el servidor (qa o prod) funcionan igual `start`, `stop`, `restart`, `logs`, `cms-logs`, `web-logs`, `contador`, `reconcile`, `shell`, `admin`, `tutor`, `backup`, `restore`, `doctor` y `config`: el ambiente lo toman de `.env`, sin `ENV=`. Dev guarda su Tutor (configuración y datos) en `.tutor-dev/`; qa y prod, en `.tutor/`. Si en el servidor copias a `.env` la plantilla de otro ambiente (qa en un servidor de prod), el comando se detiene y te dice cuál usar.

Si instalaste dev antes de `.tutor-dev/`, tu instalación vive en `.tutor/`: el primer comando de dev que corras (`make update`, `make start`...) la mueve sola a `.tutor-dev/`, con tus usuarios y cursos, y apaga los contenedores para que se recreen con la ruta nueva. Después, `make start`.

No hace falta activar ningún venv: `make` ya usa el Tutor de este repo.

Comandos del CMS (todos con `make tutor ARGS="dev exec campus-cms python manage.py ..."`):

| Comando | Para qué |
| --- | --- |
| `contador <usuario>` / `contador <usuario> --remove` | Dar o quitar el rol de contador (el usuario de Open edX) |
| `check_openedx` | Comprobar que el CMS habla con el LMS y Studio |
| `reconcile_orders` | Reintentar accesos que fallaron, cerrar pagos pendientes con Stripe y reportar inscripciones sin pago (en producción, una vez al día) |
| `test` | Correr las pruebas del CMS |

Para ver los logs del CMS: `make tutor ARGS="dev logs -f --tail=100 campus-cms"`.

---

## 9. Problemas comunes

| Síntoma | Solución |
| --- | --- |
| `make: not found` | `sudo apt install -y make` |
| `scripts/...sh: Permission denied` | `chmod +x scripts/*.sh` |
| `docker: not found` o falta `docker.sock` | Docker Desktop no está abierto. Ábrelo; si sigue igual, `wsl --shutdown` en PowerShell y ábrelo de nuevo |
| La construcción se corta con `EOF` | Falta memoria: revisa `.wslconfig`, cierra programas y repite el comando |
| Error de montaje con `redis.conf` | Quedaron contenedores viejos: `docker rm -f $(docker ps -aq --filter name=tutor_)` y repite |
| No llega el correo de activación | En dev no se envían correos. Activa al usuario en http://local.openedx.io:8000/admin/auth/user/ (casilla *Active*) o créalo con `make tutor ARGS="dev do createuser alumno1 alumno1@ejemplo.com"` |
| No abre http://www.local.openedx.io:3000 | Revisa que `make front` siga corriendo; `ss -ltnp \| grep 3000` debe mostrar `0.0.0.0:3000` |
| `make stripe` muestra `[400]` | El `whsec_` de `.env` no coincide: cópialo de nuevo y corre `make config` |
| `/admin` dice "La administración no está disponible" | El CMS no responde. Revisa http://campus-cms.local.openedx.io:8010/api/health/ y los logs del CMS; normalmente basta `make tutor ARGS="dev restart campus-cms"` |
| `/admin` dice "Esta sección es solo para contadores" | Tu usuario no tiene el rol en el CMS: `make tutor ARGS="dev exec campus-cms python manage.py contador <usuario>"` |
| Pagué y la página se queda en "Estamos activando tu acceso" | El pago llegó pero Open edX no dio el acceso. En `/admin/ventas`, filtra por acceso "Error en Open edX", lee el motivo y usa "Reintentar" (o corre `reconcile_orders`). Si no llega nada a `/admin/ventas`, revisa que `make stripe` esté corriendo |
| Un curso no aparece en Campus | Solo aparecen los cursos del CMS puestos a la venta. Uno creado directo en Studio se toma en `/admin/cursos/nuevo` → *Tomar un curso de Open edX* |
| *Contenido* dice "Tu usuario no puede editar este curso en Open edX" | No eres autor del curso. Agrégate en Studio → Configuración → Equipo del curso (lo hace alguien del equipo o un staff) |
| Al crear el curso dice "Open edX no creó el curso" | Studio tardó o falló. En la página del curso, pestaña *Precio y venta*, pulsa *Reintentar creación*: no se duplica |
| Un video subido no se reproduce | Los sirve Campus: revisa que `make front` esté corriendo |
| El menú de Open edX no cambia | Falta reconstruir la imagen de los MFE: `make tutor ARGS="images build mfe"` y `make tutor ARGS="dev start -d mfe"` |

---

## 10. Otros temas

**Un proyecto a la vez.** Cada repo guarda su Tutor en `.tutor-dev/`, así que los proyectos no se mezclan, pero usan los mismos puertos. Para cambiar: `make stop` en uno y `make start` en el otro.

**Pasar datos a otra persona.** Un curso: Studio → Herramientas → Exportar, y el otro lo importa (pero no queda a la venta: eso vive en el CMS). Todo (usuarios, cursos, progreso, del CMS los cursos a la venta, precios y ventas, y los videos subidos): `make backup`, comparte la carpeta de `backups/` y el otro corre `make restore BACKUP=backups/...`.

**Traer una instalación vieja de `~/.local/share/tutor`:**

```bash
cd ~/plataforma-equipo
TUTOR_ROOT_OVERRIDE=~/.local/share/tutor make backup
TUTOR_ROOT_OVERRIDE=~/.local/share/tutor make stop
make setup
make restore BACKUP=backups/<la carpeta que se creó>
```

---

## 11. QA y producción en un servidor (`tutor local`)

QA y producción son la plataforma completa en un servidor, como la verá la gente: HTTPS y correos de verdad. Se preparan igual; cambian el dominio y Stripe: **qa** cobra en modo de prueba (para probar el ciclo entero: registro → compra → curso) y **prod** cobra de verdad. Cada uno va en su propio servidor.

Corren con `tutor local` y **no se construyen en el servidor**: tú construyes las imágenes en tu máquina, las subes al registro de Docker del equipo y el servidor solo las baja.

| Pieza                                   | Dónde vive                                                                                                                                |
|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| Open edX (LMS, Studio, workers)         | Imagen `openedx` del registro, con el plugin del LMS (`openedx-course-payments`) instalado dentro                                         |
| MFE (con el menú y el footer de Campus) | Imagen `openedx-mfe` del registro                                                                                                         |
| CMS (`campus-cms`)                      | Imagen `campus-cms` del registro, con gunicorn                                                                                            |
| Campus (`front-campus`)                 | Imagen `campus-web` del registro (`node .output/server/index.mjs`)                                                                        |
| HTTPS                                   | Caddy de Tutor, con certificados de Let's Encrypt automáticos para todos los dominios                                                     |
| Docker compose                          | Lo genera Tutor en `.tutor/env/local/` del servidor a partir de los plugins (`tutor-plugins/campusweb.py` y `campuscms.py` agregan Campus y el CMS) |
| Configuración                           | `.env.qa` / `.env.prod` (plantillas en Git, sin llaves), `config/tutor.env` y `.env` (la copia con las llaves, solo en el servidor)       |
| Datos                                   | `.tutor/data/` en el servidor: MySQL, MongoDB, videos de Campus (`campus-web/videos`) e imágenes del CMS (`campus-cms/media`)             |

Direcciones (con los dominios de ejemplo de las plantillas; en prod quita el `qa.`):

| Qué                                        | QA                                   | Producción                        |
|--------------------------------------------|--------------------------------------|-----------------------------------|
| Campus                                     | https://www.qa.campus.example.com    | https://www.campus.example.com    |
| LMS                                        | https://qa.campus.example.com        | https://campus.example.com        |
| Studio                                     | https://studio.qa.campus.example.com | https://studio.campus.example.com |
| MFE                                        | https://apps.qa.campus.example.com   | https://apps.campus.example.com   |
| CMS (webhooks de Stripe y admin de Django) | https://cms.qa.campus.example.com    | https://cms.campus.example.com    |

Campus debe ser un subdominio del LMS (`www.` + `LMS_HOST`): lee las cookies de sesión que el LMS pone en su dominio.

### 11.1 Los archivos de configuración

| Archivo | Qué es | En Git |
| --- | --- | --- |
| `.env.dev`, `.env.qa`, `.env.prod` | Plantilla de cada ambiente: dominio, correo y las llaves vacías (`...`) | sí |
| `config/images.env` | El registro y la versión (etiqueta) de cada imagen de qa y prod | sí |
| `.env` | La copia de una plantilla con las llaves llenas | **nunca** |

- Lo que no es secreto (dominio, correo) se cambia **en la plantilla** y se hace commit: `make build` construye las imágenes con una copia de la plantilla, así que la plantilla y el `.env` del servidor deben coincidir.
- Las versiones de las imágenes se cambian en `config/images.env` (ver 11.3).
- Las llaves (Stripe, contraseña del correo) solo van en el `.env` del servidor. Nunca las escribas en `.env.qa` ni en `.env.prod`.

### 11.2 Preparar un servidor (una sola vez)

1. **El servidor.** Ubuntu con 4 CPU y 8 GB de RAM como mínimo (16 GB recomendado), 50 GB de disco. Instala Docker Engine (https://docs.docker.com/engine/install/ubuntu/) y:

   ```bash
   sudo apt install -y git make python3 python3-venv python3-pip
   sudo usermod -aG docker $USER   # vuelve a entrar por ssh después
   ```

   Abre los puertos 22, 80 y 443. Clona el repo con sus submódulos (el servidor necesita acceso de lectura a los repos de GitHub, por ejemplo con una *deploy key*):

   ```bash
   git clone --recurse-submodules git@github.com:alfonsodiazc09/plataforma-equipo.git
   ```

2. **El DNS.** Apunta a la IP del servidor el dominio y todos sus subdominios: en QA un registro `A` para `qa.campus.example.com` y otro para `*.qa.campus.example.com`.

3. **El registro de Docker.** Uno privado (Nexus, Docker Hub privado, GitHub Container Registry, el de tu nube): **las imágenes llevan los dominios de la plataforma, nunca uses uno público**. Inicia sesión en tu máquina y en el servidor:

   ```bash
   docker login registry.example.com
   ```

   La dirección a la que se suben las imágenes es `CAMPUS_DOCKER_REGISTRY` en `config/images.env`, sin `/` al final: forma parte del nombre de cada imagen (`nexus.getechnologiesmx.com/docker-releases/auditia/educacion/campus-web:20261031-81b53f5`), y `docker push` la sube al servidor que va antes de la primera `/`. Para Nexus usa el puerto de su repositorio Docker (`nexus.tuempresa.com:8083/campus`); para Docker Hub, `docker.io/<tu-usuario>`; para GitHub, `ghcr.io/<org>`.

4. **La plantilla.** En tu máquina, en `.env.qa` (o `.env.prod`), cambia el dominio y el correo (sin `http://`: `LMS_HOST=qa.tudominio.com`); en `config/images.env`, el registro. Haz commit y push.

5. **El `.env` del servidor.** Ya en el servidor (`cd plataforma-equipo`):

   ```bash
   cp .env.qa .env     # en producción: cp .env.prod .env
   nano .env           # llena las llaves que terminan en ...
   ```

   `make deploy` no arranca mientras quede alguna llave en `...`.

6. **Stripe.** En el dashboard de Stripe (modo de prueba en QA, https://dashboard.stripe.com/test/webhooks; modo real en producción) → *Add endpoint*: URL `https://cms.<dominio>/api/v1/webhooks/stripe/` y los eventos `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired` y `charge.refunded`. Copia su *Signing secret* (`whsec_...`) a `CAMPUS_CMS_STRIPE_WEBHOOK_SECRET` en el `.env` del servidor. En el servidor no se usa `make stripe`.

7. **El correo.** El relevo de correo de Tutor manda por el puerto 25, que casi todos los servidores bloquean, así que se usa un proveedor (`SMTP_*` en la plantilla; usuario y contraseña en `.env`). Sin correo, nadie puede activar su cuenta ni recuperar su contraseña. Verifica en el proveedor el remitente `CONTACT_EMAIL`.

### 11.3 Publicar una versión

Son dos comandos: `make build` en tu máquina y `make deploy` en el servidor. Los dos toman el ambiente de `CAMPUS_ENV` en `.env`.

**Las versiones.** `config/images.env` tiene una etiqueta por imagen. Para publicar un cambio, sube **solo** la etiqueta de la imagen que cambió:

| Imagen | Etiqueta | Cuándo cambiarla | Convención |
| --- | --- | --- | --- |
| `openedx` | `OPENEDX_IMAGE_TAG` | Cambió el plugin del LMS (`openedx-course-payments`), `config/tutor.env` (tema, colores) o la versión de Tutor | `21.0.9-20261031` |
| `openedx-mfe` | `MFE_IMAGE_TAG` | Cambió el menú o el footer de Campus (`tutor-plugins/campusmenu.py`) o el dominio de Campus | `21.0.2-20261031` |
| `campus-cms` | `CAMPUS_CMS_IMAGE_TAG` | Cambió `src/campus-cms` | `20261031-<commit>` |
| `campus-web` | `CAMPUS_WEB_IMAGE_TAG` | Cambió `src/front-campus` | `20261031-<commit>` |

`<commit>` es `git -C src/campus-cms rev-parse --short HEAD` (o `src/front-campus`). Open edX, el CMS y Campus son la misma imagen en qa y prod: producción corre exactamente lo que se probó en QA. Los MFE llevan compilada la dirección de Campus, así que su imagen termina en `-qa` o `-prod` y cada ambiente construye la suya.

**1. En tu máquina**, con el código en el commit que quieres publicar (y ya en GitHub):

```bash
cp .env .env.local    # guarda tu .env de dev (.env.local tampoco se sube a Git)
cp .env.qa .env       # o .env.prod: CAMPUS_ENV=qa (o prod)
make build            # construye y sube solo las imágenes cuya etiqueta no está en el registro
cp .env.local .env    # regresa a dev
git commit -am "Imágenes: ..." && git push   # config/images.env, para que el servidor las baje
```

`make build` revisa en el registro cada imagen de `config/images.env`: las que ya están se omiten y solo construye las nuevas (si no cambiaste nada, no hace nada). Una etiqueta publicada no se reconstruye: cada cambio lleva etiqueta nueva. Si el CMS o Campus tienen cambios sin commit, avisa. Al pasar a producción, `make build` con `.env.prod` normalmente solo construye su MFE.

`make build` no necesita llaves (no entran en las imágenes) y usa un Tutor temporal que se borra al terminar: no toca `.tutor-dev/`. Mientras construye, apaga dev (`make stop`) si tu máquina tiene poca memoria. Con un `.env` de dev, `make build` se niega.

**2. En el servidor** (`ssh` y `cd plataforma-equipo`):

```bash
make deploy
```

`make deploy` (`scripts/deploy.sh`) hace todo, en orden:

1. Baja el código: `git pull` y los submódulos.
2. Instala Tutor si falta y aplica `.env`.
3. Baja las imágenes del registro, genera el docker compose y lo enciende con `tutor local`.
4. Corre `do init`: migraciones, base del CMS y su cuenta de servicio en el LMS.

Es seguro repetirlo: la segunda vez solo actualiza. No arranca mientras quede alguna llave en `...`.

Si el código nuevo trae cambios en la plantilla (`.env.qa` o `.env.prod`), pásalos a tu `.env` del servidor y vuelve a correr `make deploy` (`git diff HEAD@{1} -- .env.qa` muestra qué cambió).

La primera vez, ya en el servidor:

```bash
make admin USER_NAME=admin EMAIL=tu@correo.com
make contador USER_NAME=admin
```

Y programa la conciliación diaria de pagos (`crontab -e`):

```cron
0 3 * * * cd ~/plataforma-equipo && make reconcile >> ~/reconcile.log 2>&1
```

Para regresar a una versión anterior, vuelve a poner su etiqueta en `config/images.env` (ya está en el registro: no hay que construir), haz commit y corre `make deploy` en el servidor.

### 11.4 Probar el ciclo completo (en QA)

1. **Registro:** en Campus pulsa *Registrarse*, crea una cuenta y actívala con el correo que llega.
2. **Curso:** con el usuario contador entra a `/admin`, crea un curso, arma su contenido (sube un video), publícalo, ponle precio e imagen y ponlo a la venta.
3. **Compra:** con el alumno, compra el curso con la tarjeta de prueba `4242 4242 4242 4242`. En `/admin/ventas` aparece pagado y con acceso; en Stripe → Webhooks, el evento con respuesta 200.
4. **Aprendizaje:** el alumno entra al curso desde *Mis cursos* y ve el video.

### 11.5 Operar el servidor

| Para qué | Comando |
| --- | --- |
| Cambié una llave | Edita `.env` en el servidor y `make config` |
| Cambié el dominio, el registro o el correo | En la plantilla (commit y push) y en el `.env` del servidor, y `make config`. Si cambió el dominio de Campus o el footer, antes `make build` y después `make deploy` (el menú de los MFE se compila en su imagen) |
| Ver errores | `make logs`, `make cms-logs`, `make web-logs` |
| Estado | `make doctor` |
| Respaldo / restaurar | `make backup` / `make restore BACKUP=backups/qa-...` |
| Apagar / encender | `make stop` / `make start` |
| Cualquier comando de Tutor | `make tutor ARGS="local ..."` |

Los secretos que genera Tutor (contraseñas de MySQL, la llave de Django, la del CMS) viven solo en `.tutor/config.yml` del servidor: entran en el respaldo si copias esa carpeta, no en `make backup`. Guarda también una copia de `.env` fuera del servidor (no en Git).

### 11.6 Problemas comunes en el servidor

| Síntoma | Solución |
| --- | --- |
| El navegador dice que el certificado no es válido | El DNS aún no apunta al servidor o los puertos 80/443 están cerrados. Revisa `make tutor ARGS="local logs caddy"` |
| `make deploy` dice `pull access denied` | Falta `docker login` en el servidor, o la etiqueta de `config/images.env` no se publicó: corre `make build` con el `.env` de ese ambiente (y haz commit/push de `config/images.env`) |
| `Este .tutor/ es del ambiente ...` | El `.env` es copia de otra plantilla: copia la de este servidor y vuelve a llenar las llaves |
| No llega el correo de activación | Revisa `SMTP_*` y la contraseña en `.env`, y `make logs` (busca `SMTP`) |
| Campus no muestra quién inició sesión | Campus no es subdominio de `LMS_HOST`, o falta HTTPS: revisa `CAMPUS_WEB_URL` en `.env` |
| Pagué y el acceso no llega | En Stripe → Webhooks revisa el endpoint: un 400 es un `whsec_` equivocado en `.env` (corrígelo y `make config`) |
| El menú de Open edX lleva a otro dominio | Se compiló con otro `CAMPUS_WEB_URL`: `make build` y `make deploy` |
