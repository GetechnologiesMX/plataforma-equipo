Aquí van los plugins de Tutor del equipo (archivos `.py` o `.yml`).
Cada archivo se activa automáticamente con `make setup` o `make update`.

Si un plugin monta código de `src/`, debe declarar el nombre de la carpeta para que Tutor lo instale
dentro de la imagen, por ejemplo:

    from tutor import hooks
    hooks.Filters.MOUNTED_DIRECTORIES.add_item(("openedx", "plugin-stripe"))

| Plugin | Qué hace |
| --- | --- |
| `campuscms.py` | Enlace a `src/campus-cms/tutor/campuscms.py`: el CMS en `tutor dev` y en `tutor local` (QA) |
| `coursepayments.py` | Enlace a `src/openedx-course-payments/tutor/coursepayments.py`: ajustes del plugin del LMS |
| `campusmenu.py` | Menú, logo y footer de Campus en los MFE (se compila en la imagen `mfe`) |
| `campusweb.py` | Campus (Nuxt) como contenedor en `tutor local` (QA), detrás de Caddy |
| `campustheme.py` | Colores de Campus en los MFE (botones, links, formularios): carga `src/front-campus/public/theme/campus-paragon.css` encima del tema de Indigo. Va en la configuración del LMS, no en la imagen: basta `make config` |
