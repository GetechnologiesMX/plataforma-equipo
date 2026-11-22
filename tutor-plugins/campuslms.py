"""
Tutor plugin: Campus header, footer and catalog in the legacy LMS pages.

The LMS still renders some pages with Django/Mako templates instead of an MFE:
the course catalog (/courses), /about, /tos... and the course pages that have
no MFE (instructor dashboard, wiki...). They use tutor-indigo's theme, with its
own header, footer and texts hardcoded in English.

This plugin puts its own versions of those templates in front of Indigo's: same
paths under tutor-plugins/campuslms/indigo/, and a template root with higher
priority, so Tutor renders them into the Indigo theme instead of Indigo's
(env/build/openedx/themes/indigo):

- header/header.html: the Campus header (logo, Mis cursos / Cursos / Eventos /
  Administración, user menu or Iniciar sesión / Crear cuenta).
- footer.html: the Campus footer (contact, address and map), with CAMPUS_FOOTER
  and CAMPUS_MENU_SITE_URL from tutor-plugins/campusmenu.py.
- courseware/courses.html and discovery/course_card.underscore: /courses in
  Spanish (filters too) with the cards of Campus /cursos.

The styles go inline in the templates: no theme (Sass) compilation needed.

Applying it:
- local (tutor dev): `make config`; the theme folder is mounted in the LMS.
- dev, qa and prod: the theme is part of the openedx image (`make build`).
"""
import os

from tutor import hooks

# Before tutor-indigo's root (default priority): for the same template path,
# Tutor's Jinja loader takes the first root that has it.
hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "campuslms"),
    priority=hooks.priorities.HIGH,
)
