"""
Tutor plugin: Campus main menu in the Open edX MFE headers.

- Replaces the default main menu ("Courses", "Programs", ...) with links to the
  public Campus site (mis-cursos, cursos, eventos).
- Staff users (`is_staff`) also see "Administración" (Campus admin).
- Desktop and mobile headers, plus the course header of the `learning` MFE.
- Replaces the logo with the public site's (its public/logo.svg) and gives
  every MFE header the white compliance-v2 look (`--campus-header-*`), with
  the same colors and metrics as the public Nuxt site.
- Replaces the footer with the public site's (contact, address and map), in
  the same MFEs as the Campus header.
- Studio (the `authoring` MFE) has its own header, with the course menus
  (Contenido, Configuración, Herramientas): it keeps them, with the Campus
  look and logo, a "Campus" dropdown with the Campus links next to the user
  menu (everything in one row) and the Campus footer.
- The `LOGO_*` of the MFE config point to the Campus logo, for the MFEs that
  draw it from there (Studio, login/registration, admin console).
- Learner dashboard: course cards with the Campus look, without the green
  "verified" ribbon that stuck out of the course image.

The legacy LMS pages (/courses, /about...) get the same header and footer from
tutor-plugins/campuslms.py.

The menu is compiled into the MFE image, so after changing it:
    tutor images build mfe && tutor dev start -d mfe
The `LOGO_*` settings go to the LMS instead: `make config`.

The JS uses aliased imports and `createElement` instead of JSX so it does not
clash with (or depend on) the identifiers that tutor-indigo imports.
"""
from tutor import hooks
from tutormfe.hooks import PLUGIN_SLOTS

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Public (Nuxt) site the menu links to.
        ("CAMPUS_MENU_SITE_URL", "http://www.local.openedx.io:3000"),
        # MFEs with the Campus header and footer, where the Campus logo replaces Indigo's.
        (
            "CAMPUS_HEADER_MFES",
            [
                "learner-dashboard",
                "profile",
                "account",
                "learning",
                "communications",
                "discussions",
                "gradebook",
                "ora-grading",
            ],
        ),
        # Footer contact details. Placeholders, the same as the public site's
        # (`contact` in app/layouts/default.vue): change both together.
        (
            "CAMPUS_FOOTER",
            {
                "email": "contacto@local.openedx.io",
                "phone": "+52 55 1234 5678",
                "hours": "Lunes a viernes, 9:00 a 18:00",
                "address": [
                    "Av. Paseo de la Reforma 222, piso 5",
                    "Col. Juárez, Cuauhtémoc",
                    "06600 Ciudad de México, CDMX",
                ],
                "lat": 19.4285,
                "lon": -99.1617,
            },
        ),
    ]
)

hooks.Filters.ENV_PATCHES.add_items(
    [
        (
            "mfe-env-config-buildtime-imports",
            """
import { createElement as campusH, useContext as campusUseContext } from 'react';
import { Dropdown as CampusDropdown } from '@openedx/paragon';
import { AppContext as CampusAppContext } from '@edx/frontend-platform/react';
""",
        ),
        (
            "mfe-env-config-buildtime-definitions",
            """
const campusSite = '{{ CAMPUS_MENU_SITE_URL }}'.replace(/\\/$/, '');

const campusMenuLinks = (user) => {
  const site = campusSite;
  const links = [
    { id: 'mis-cursos', label: 'Mis cursos', href: `${site}/mis-cursos` },
    { id: 'cursos', label: 'Cursos', href: `${site}/cursos` },
    { id: 'eventos', label: 'Eventos', href: `${site}/eventos` },
  ];
  if (user && user.administrator) {
    links.push({ id: 'admin', label: 'Administración', href: `${site}/admin` });
  }
  return links;
};

const CampusMenuLinks = ({ className }) => {
  const { authenticatedUser } = campusUseContext(CampusAppContext);
  return campusH(
    'nav',
    { 'aria-label': 'Principal', className },
    campusMenuLinks(authenticatedUser).map((link) => campusH(
      'a',
      { key: link.id, className: 'nav-link', href: link.href },
      link.label,
    )),
  );
};

const CampusMainMenu = () => campusH(CampusMenuLinks, { className: 'nav main-nav' });

const CampusMobileMainMenu = () => campusH(CampusMenuLinks, { className: 'nav flex-column' });

const CampusLearningMenu = () => campusH(CampusMenuLinks, { className: 'nav d-none d-md-flex mr-2' });

// Studio header: its course menus (Contenido, Configuración, Herramientas) are the
// work tools and stay in sight; the Campus links, which leave Studio, go together
// in one "Campus" dropdown next to the user menu, so everything fits in one row.
// Same Paragon dropdown as Studio's menus (keyboard, closes on outside click).
const CampusStudioMenu = () => {
  const { authenticatedUser } = campusUseContext(CampusAppContext);
  const links = campusMenuLinks(authenticatedUser);
  return campusH(
    CampusDropdown,
    { className: 'campus-studio-menu' },
    campusH(
      CampusDropdown.Toggle,
      { id: 'campus-studio-menu', variant: 'outline-primary' },
      'Campus',
    ),
    campusH(
      CampusDropdown.Menu,
      { align: 'right' },
      links.map((link) => [
        link.id === 'admin' && campusH(CampusDropdown.Divider, { key: 'admin-divider' }),
        campusH(CampusDropdown.Item, { key: link.id, href: link.href }, link.label),
      ]),
    ),
  );
};

// Same logo file as the public site (its public/logo.svg), linking to its home.
const CampusLogo = () => campusH(
  'a',
  { className: 'campus-logo', href: `${campusSite}/` },
  campusH('img', { src: `${campusSite}/logo.svg`, alt: 'Campus' }),
);

// tutor-indigo replaces the whole mobile header with just its logo (hidden
// below, in runtime-final), so the mobile main menu slot never renders there:
// this is the replacement, a bar with the logo and a collapsible menu.
const CampusMobileHeaderMenu = () => campusH(
  'div',
  { className: 'campus-mobile-header' },
  campusH('style', null, `
    .campus-mobile-header {
      position: relative; z-index: 1000; display: flex; justify-content: space-between; align-items: center;
      min-height: 64px; padding: 0 16px;
      background: var(--campus-header-bg); border-bottom: 1px solid var(--campus-header-border);
    }
    .campus-mobile-menu { position: relative; }
    .campus-mobile-menu > summary {
      cursor: pointer; list-style: none; padding: .375rem .75rem; color: var(--campus-header-text);
      border: 1px solid var(--campus-header-control-border); border-radius: 999px;
    }
    .campus-mobile-menu > summary::-webkit-details-marker { display: none; }
    .campus-mobile-menu > nav {
      position: absolute; top: calc(100% + .5rem); right: 0; min-width: 12rem; padding: .5rem 0;
      background: var(--campus-header-bg); border: 1px solid var(--campus-header-border);
      border-radius: .375rem; box-shadow: 0 14px 26px rgba(0, 0, 0, .08);
    }
    .campus-mobile-menu > nav .nav-link { color: var(--campus-header-link); }
    .campus-mobile-menu > nav .nav-link:hover { color: var(--campus-header-text); background: var(--campus-header-hover); }
  `),
  campusH(CampusLogo),
  campusH(
    'details',
    { className: 'campus-mobile-menu' },
    campusH('summary', null, 'Menú'),
    campusH(CampusMenuLinks, { className: 'nav flex-column' }),
  ),
);

const campusFooter = {{ CAMPUS_FOOTER | tojson }};

// Same footer as the public Nuxt site (app/layouts/default.vue): brand, contact,
// address and an OpenStreetMap map (no API key needed).
const CampusFooter = () => {
  const { lat, lon } = campusFooter;
  const mapEmbedUrl = `https://www.openstreetmap.org/export/embed.html?bbox=${lon - 0.006},${lat - 0.004},${lon + 0.006},${lat + 0.004}&layer=mapnik&marker=${lat},${lon}`;
  const mapLinkUrl = `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=17/${lat}/${lon}`;
  return campusH(
    'footer',
    { className: 'campus-footer' },
    campusH('style', null, `
      #root .campus-footer {
        padding: 48px 0 24px; font-size: 1rem; line-height: 1.5;
        background: var(--campus-footer-bg); border-top: 1px solid var(--campus-header-border);
        color: var(--campus-footer-text);
      }
      #root .campus-footer-container { max-width: 1120px; margin: 0 auto; padding: 0 16px; }
      #root .campus-footer-grid { display: grid; gap: 32px; }
      #root .campus-footer .campus-logo img { display: block; height: 28px; }
      #root .campus-footer-brand p { margin: 12px 0 16px; }
      #root .campus-footer-nav { display: flex; gap: 24px; }
      #root .campus-footer h2 {
        margin: 0 0 12px; font-size: .875rem; font-weight: 600; letter-spacing: .04em;
        text-transform: uppercase; color: var(--campus-header-text);
      }
      #root .campus-footer-list {
        display: flex; flex-direction: column; gap: 8px; margin: 0; padding: 0;
        list-style: none; font-style: normal;
      }
      #root .campus-footer a { color: var(--campus-footer-text); text-decoration: none; }
      #root .campus-footer a:hover { color: var(--campus-link); text-decoration: underline; }
      #root .campus-footer-map-link { display: inline-block; margin-top: 12px; font-weight: 500; }
      #root .campus-footer iframe {
        display: block; width: 100%; height: 200px;
        border: 1px solid var(--campus-header-border); border-radius: .375rem;
      }
      #root .campus-footer-bottom {
        margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--campus-header-border);
        font-size: .875rem; color: var(--campus-header-link);
      }
      @media (min-width: 640px) {
        #root .campus-footer-grid { grid-template-columns: 1fr 1fr; }
      }
      @media (min-width: 900px) {
        #root .campus-footer-grid { grid-template-columns: 1.2fr 1fr 1fr 1.4fr; }
      }
    `),
    campusH(
      'div',
      { className: 'campus-footer-container campus-footer-grid' },
      campusH(
        'div',
        { className: 'campus-footer-brand' },
        campusH(CampusLogo),
        campusH('p', null, 'Cursos en línea con acceso de por vida.'),
        campusH(
          'nav',
          { className: 'campus-footer-nav', 'aria-label': 'Pie de página' },
          campusH('a', { href: `${campusSite}/cursos` }, 'Cursos'),
          campusH('a', { href: `${campusSite}/eventos` }, 'Eventos'),
        ),
      ),
      campusH(
        'div',
        null,
        campusH('h2', null, 'Contacto'),
        campusH(
          'ul',
          { className: 'campus-footer-list' },
          campusH('li', null, campusH('a', { href: `mailto:${campusFooter.email}` }, campusFooter.email)),
          campusH('li', null, campusH('a', { href: `tel:${campusFooter.phone.replace(/\\s/g, '')}` }, campusFooter.phone)),
          campusH('li', null, campusFooter.hours),
        ),
      ),
      campusH(
        'div',
        null,
        campusH('h2', null, 'Dirección'),
        campusH(
          'address',
          { className: 'campus-footer-list' },
          campusFooter.address.map((line) => campusH('span', { key: line }, line)),
        ),
        campusH('a', { className: 'campus-footer-map-link', href: mapLinkUrl, target: '_blank', rel: 'noopener' }, 'Cómo llegar'),
      ),
      campusH(
        'div',
        null,
        campusH('iframe', {
          src: mapEmbedUrl, title: 'Mapa de la ubicación de Campus', loading: 'lazy', referrerPolicy: 'no-referrer',
        }),
      ),
    ),
    campusH(
      'div',
      { className: 'campus-footer-container campus-footer-bottom' },
      `© ${new Date().getFullYear()} Campus. Todos los derechos reservados.`,
    ),
  );
};

// White header in every MFE (desktop, mobile and course headers), like
// compliance-v2 and the public Nuxt site. Colors from tema-compliance.css; the
// public site uses the same ones (app/layouts/default.vue). Added once when
// the MFE loads; `#root` and `!important` are needed to beat tutor-indigo's
// header styles.
if (typeof document !== 'undefined' && !document.getElementById('campus-header-styles')) {
  const campusHeaderStyles = document.createElement('style');
  campusHeaderStyles.id = 'campus-header-styles';
  campusHeaderStyles.textContent = `
    :root {
      --campus-header-bg: #fff;                   /* --header-bg */
      --campus-header-border: #e6eff5;            /* --header-border */
      --campus-header-text: #101010;              /* --color-text-strong: active item, user */
      --campus-header-link: #606060;              /* --color-text-navigation: inactive items */
      --campus-header-hover: #f8f7f6;             /* --menu-item-active-bg */
      --campus-header-control-border: #bac7d5;    /* --color-border-input */
      --campus-header-active: #9b8467;            /* --color-primary: active underline */
      --campus-footer-bg: #f9fafb;                /* --footer-bg */
      --campus-footer-text: #555;                 /* --color-text-body */
      --campus-link: #0a19cd;                     /* --color-accent */
    }
    #root header.site-header-desktop,
    #root header.site-header-mobile,
    #root header.learning-header {
      background: var(--campus-header-bg);
      color: var(--campus-header-text);
      box-shadow: none;
      border-bottom: 1px solid var(--campus-header-border);
    }
    #root header.site-header-desktop .main-nav a.nav-link,
    #root header.learning-header .nav a.nav-link {
      color: var(--campus-header-link);
    }
    #root header.site-header-desktop .btn-link,
    #root header.learning-header .course-title-lockup,
    #root header.learning-header .course-title-lockup .title,
    #root header.learning-header .course-title-lockup .org,
    #root header.learning-header .text-gray-700,
    #root header.site-header-mobile .icon-button {
      color: var(--campus-header-text);
    }
    /* Same metrics as the public Nuxt site header (app/layouts/default.vue). */
    #root header.site-header-desktop .container-fluid {
      max-width: none;
      padding: 0 24px;
    }
    #root header .campus-logo {
      display: flex;
      align-items: center;
      flex-shrink: 0;
      margin-right: 32px;
    }
    #root header .campus-logo img,
    #root .campus-mobile-header .campus-logo img {
      display: block;
      height: 28px;
    }
    #root header.site-header-desktop .main-nav a.nav-link {
      padding: 20px 0 18px;
      margin: 0 24px 0 0;
      font-size: 1rem;
      font-weight: 500;
      line-height: 24px;
      border-bottom: 2px solid transparent;
    }
    #root header.site-header-desktop .main-nav a.nav-link:hover,
    #root header.site-header-desktop .main-nav a.nav-link:focus,
    #root header.learning-header .nav a.nav-link:hover,
    #root header.learning-header .nav a.nav-link:focus {
      color: var(--campus-header-text);
      background: transparent;
      text-decoration: none;
      border-bottom-color: var(--campus-header-active);
    }
    #root header.site-header-desktop .main-nav a.nav-link.active {
      color: var(--campus-header-text);
      background: transparent;
      border-bottom-color: var(--campus-header-active);
    }
    #root header.site-header-desktop .menu > button,
    #root header.site-header-desktop .btn-outline-primary,
    #root header.learning-header .user-dropdown > button,
    #root header.learning-header .btn-outline-primary {
      background: transparent !important;
      color: var(--campus-header-text) !important;
      border: 1px solid var(--campus-header-control-border) !important;
    }
    #root header.site-header-desktop .menu > button:hover,
    #root header.site-header-desktop .btn-outline-primary:hover,
    #root header.learning-header .user-dropdown > button:hover,
    #root header.learning-header .btn-outline-primary:hover {
      background: var(--campus-header-hover) !important;
    }
    #root header.learning-header .user-dropdown > button::after {
      border-color: var(--campus-header-text) !important;
    }
    #root header.site-header-mobile .icon-button:hover,
    #root header.site-header-mobile .icon-button:focus {
      background: var(--campus-header-hover);
    }
    #root header .hamburger-menu .line {
      background: var(--campus-header-text);
    }
    #root header.site-header-mobile .menu-content,
    #root header.site-header-mobile .nav.flex-column {
      background: var(--campus-header-bg);
    }
    #root header.site-header-mobile .menu-content a,
    #root header.site-header-mobile .nav.flex-column .nav-link {
      color: var(--campus-header-link);
    }
    #root header.site-header-mobile .menu-content a:hover {
      background: var(--campus-header-hover);
      color: var(--campus-header-text);
    }

    /* Studio (authoring MFE): its own header, with the same look. */
    #root .studio-header {
      height: auto;
      background: var(--campus-header-bg);
      box-shadow: none;
      border-bottom: 1px solid var(--campus-header-border);
    }
    #root .studio-header > .container-xl {
      max-width: none;
      padding: 0 24px !important;
    }
    #root .studio-header header.pgn__action-row {
      min-height: 64px;
    }
    #root .studio-header .logo {
      height: 28px;
      padding: 18px 0;
      margin-right: 24px;
    }
    #root .studio-header .course-title-lockup {
      border-right-color: var(--campus-header-border);
    }
    #root .studio-header .course-title-lockup span {
      color: var(--campus-header-text) !important;
    }
    #root .studio-header .dropdown > .btn-outline-primary,
    #root .studio-header .btn-tertiary {
      background: transparent !important;
      color: var(--campus-header-link) !important;
      border: 1px solid transparent !important;
      font-weight: 500;
      box-shadow: none !important;
    }
    #root .studio-header .dropdown > .btn-outline-primary:hover,
    #root .studio-header .dropdown > .btn-outline-primary[aria-expanded="true"],
    #root .studio-header .btn-tertiary:hover {
      color: var(--campus-header-text) !important;
      background: var(--campus-header-hover) !important;
    }
    /* The user menu, like the Campus user button. */
    #root .studio-header #user-dropdown-menu {
      color: var(--campus-header-text) !important;
      border-color: var(--campus-header-control-border) !important;
    }
    /* One row always: the menus never wrap (Bootstrap's .nav does) and the
       course title (logo + lockup, a fixed 25% in Studio) is what gives way,
       cut with an ellipsis. */
    #root .studio-header header.pgn__action-row,
    #root .studio-header header.pgn__action-row .nav {
      flex-wrap: nowrap;
    }
    #root .studio-header header.pgn__action-row > .w-25 {
      flex: 0 1 25%;
      width: auto !important;
      min-width: 0;
    }
    #root .studio-header header.pgn__action-row > .w-25 .logo {
      flex-shrink: 0;
    }
    #root .studio-header .dropdown > .btn {
      white-space: nowrap;
    }
    /* The Campus dropdown, next to the user menu. */
    #root .studio-header .campus-studio-menu {
      flex-shrink: 0;
      margin-right: 8px;
    }
    #root .studio-header .campus-studio-menu .dropdown-menu {
      min-width: 12rem;
    }
    #root .studio-header .campus-studio-menu .dropdown-item {
      color: var(--campus-header-link);
    }
    #root .studio-header .campus-studio-menu .dropdown-item:hover,
    #root .studio-header .campus-studio-menu .dropdown-item:focus {
      color: var(--campus-header-text);
      background: var(--campus-header-hover);
    }

    /* Learner dashboard: course cards like the Campus ones. */
    #root .course-card .pgn__card {
      overflow: hidden;
      border: 1px solid #e8e9ea;
      border-radius: 12px;
      box-shadow: 0 1px 2px rgb(37 42 49 / 6%), 0 4px 16px rgb(37 42 49 / 6%);
      transition: box-shadow .2s ease;
    }
    #root .course-card .pgn__card:hover {
      box-shadow: 0 2px 4px rgb(37 42 49 / 8%), 0 8px 24px rgb(37 42 49 / 10%);
    }
    #root .course-card .pgn__card-wrapper-image-cap {
      position: relative;
      overflow: hidden !important;
      background: #f5f3f1;
    }
    #root .course-card .pgn__card-image-cap {
      height: 100%;
      min-height: 160px;
      object-fit: cover;
      border-radius: 0 !important;
    }
    #root .course-card .course-card-title {
      color: #252a31;
      font-weight: 600;
      text-decoration: none;
    }
    #root .course-card a.course-card-title:hover {
      color: #7c6a52;
    }
    /* "Verified": a small label on the image instead of the green ribbon
       (verified-ribbon.png), which stuck out of the image's corner. */
    #root .course-card .course-card-verify-ribbon-container {
      top: 12px;
      left: 12px;
      bottom: auto;
      width: auto;
      text-align: left;
    }
    #root .course-card .course-card-verify-ribbon-container > img {
      display: none;
    }
    #root .course-card .course-card-verify-ribbon-container .badge {
      width: auto !important;
      padding: 4px 10px;
      border: 1px solid #e5e0da;
      border-radius: 999px !important;
      background: rgb(255 255 255 / 94%);
      color: #6c5c48;
      font-size: .75rem;
      font-weight: 600;
      letter-spacing: .02em;
      box-shadow: 0 1px 2px rgb(37 42 49 / 10%);
    }
  `;
  document.head.appendChild(campusHeaderStyles);
}
""",
        ),
        (
            # Runs after every MFE's slots, so it also replaces the logos that
            # tutor-indigo inserts per MFE: `custom_logo` in the desktop header and
            # its logo-only mobile header (`theme_switch_button`, replaced by
            # CampusMobileHeaderMenu).
            # The Campus logo, header and footer only go in the
            # frontend-component-header MFEs. Others keep Indigo's: authn
            # (login/register), authoring (Studio has its own header) and
            # admin-console.
            "mfe-env-config-runtime-final",
            """
    if ({{ CAMPUS_HEADER_MFES | tojson }}.includes(process.env.APP_ID)) {
      addPlugins(config, 'logo_slot', [
        { op: PLUGIN_OPERATIONS.Hide, widgetId: 'default_contents' },
        { op: PLUGIN_OPERATIONS.Hide, widgetId: 'custom_logo' },
        {
          op: PLUGIN_OPERATIONS.Insert,
          widget: { id: 'campus_logo', type: DIRECT_PLUGIN, RenderWidget: CampusLogo },
        },
      ]);
      // Indigo's footer (`indigo_footer`) is hidden too; its `read_theme_cookie`
      // widget stays.
      addPlugins(config, 'org.openedx.frontend.layout.footer.v1', [
        { op: PLUGIN_OPERATIONS.Hide, widgetId: 'default_contents' },
        { op: PLUGIN_OPERATIONS.Hide, widgetId: 'indigo_footer' },
        {
          op: PLUGIN_OPERATIONS.Insert,
          widget: { id: 'campus_footer', type: DIRECT_PLUGIN, priority: 1, RenderWidget: CampusFooter },
        },
      ]);
    }
    addPlugins(config, 'mobile_header_slot', [
      { op: PLUGIN_OPERATIONS.Hide, widgetId: 'theme_switch_button' },
    ]);
""",
        ),
    ]
)


# Campus logo for the MFEs that take it from the config instead of a plugin slot
# (Studio's header, admin console...). LMS settings: `make config`, no MFE rebuild.
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-common-settings",
        """
# Campus logo in the MFEs (tutor-plugins/campusmenu.py).
for _campus_logo_key in ("LOGO_URL", "LOGO_WHITE_URL", "LOGO_TRADEMARK_URL"):
    MFE_CONFIG[_campus_logo_key] = "{{ CAMPUS_MENU_SITE_URL.rstrip('/') }}/logo.svg"
""",
    )
)


def _replace_slot(mfe: str, slot: str, widget_id: str, component: str) -> list[tuple[str, str, str]]:
    return [
        (mfe, slot, "{ op: PLUGIN_OPERATIONS.Hide, widgetId: 'default_contents' }"),
        (
            mfe,
            slot,
            f"""
            {{
              op: PLUGIN_OPERATIONS.Insert,
              widget: {{ id: '{widget_id}', type: DIRECT_PLUGIN, RenderWidget: {component} }},
            }}""",
        ),
    ]


def _insert_into_slot(mfe: str, slot: str, widget_id: str, component: str) -> tuple[str, str, str]:
    return (
        mfe,
        slot,
        f"""
        {{
          op: PLUGIN_OPERATIONS.Insert,
          widget: {{ id: '{widget_id}', type: DIRECT_PLUGIN, priority: 90, RenderWidget: {component} }},
        }}""",
    )


PLUGIN_SLOTS.add_items(
    [
        # Studio: Campus footer (tutor-indigo's `read_theme_cookie` widget stays) and
        # the "Campus" dropdown before the search button.
        *_replace_slot("authoring", "org.openedx.frontend.layout.studio_footer.v1", "campus_footer", "CampusFooter"),
        (
            "authoring",
            "org.openedx.frontend.layout.studio_header_search_button_slot.v1",
            """
        {
          op: PLUGIN_OPERATIONS.Insert,
          widget: { id: 'campus_studio_menu', type: DIRECT_PLUGIN, priority: 5, RenderWidget: CampusStudioMenu },
        }""",
        ),
        *_replace_slot("all", "desktop_main_menu_slot", "campus_main_menu", "CampusMainMenu"),
        *_replace_slot("all", "mobile_main_menu_slot", "campus_mobile_main_menu", "CampusMobileMainMenu"),
        # Course pages use the learning header, which has no main menu slot.
        _insert_into_slot("learning", "learning_help_slot", "campus_learning_menu", "CampusLearningMenu"),
        # MFEs where tutor-indigo replaces the mobile header (see CampusMobileHeaderMenu).
        *[
            _insert_into_slot(mfe, "mobile_header_slot", "campus_mobile_header_menu", "CampusMobileHeaderMenu")
            for mfe in ["learner-dashboard", "profile", "account"]
        ],
    ]
)
