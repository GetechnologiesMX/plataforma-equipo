"""
Tutor plugin: Campus colors in the Open edX MFEs (buttons, links, forms...).

The MFEs take their colors from Paragon design tokens, loaded at runtime from
the URLs in `MFE_CONFIG["PARAGON_THEME_URLS"]`. tutor-indigo points them at
its own theme (Indigo blue and magenta); `INDIGO_PRIMARY_COLOR` only reaches
the legacy LMS/Studio pages and emails, not the MFEs.

This plugin keeps Indigo's theme as the base and adds the Campus theme on top
as the light variant's `brandOverride`: a CSS file served by the public site
(src/front-campus/public/theme/campus-paragon.css). frontend-platform inserts
it right after Indigo's, so it only redefines what Campus changes.

It is part of the LMS settings (MFE config API), not of the MFE image:
changing the CSS needs no rebuild, and changing this plugin only needs
`make config` (restarts the LMS).
"""
from tutor import hooks

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Campus Paragon theme. Override it to test another file.
        ("CAMPUS_THEME_PARAGON_URL", "{{ CAMPUS_WEB_URL }}/theme/campus-paragon.css"),
        # Logo at the top of the LMS emails (password reset, activation...). PNG, not
        # SVG: Gmail and Outlook don't show SVG images. Generated from public/logo.svg
        # (src/front-campus/public/email-logo.png). Without it, emails use Indigo's logo.
        ("CAMPUS_THEME_EMAIL_LOGO_URL", "{{ CAMPUS_WEB_URL }}/email-logo.png"),
    ]
)

hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Campus logo in the emails (tutor-plugins/campustheme.py).
LOGO_URL_PNG_FOR_EMAIL = "{{ CAMPUS_THEME_EMAIL_LOGO_URL }}"
""",
    )
)

# LOW priority: it must render after tutor-indigo's patch, which sets
# PARAGON_THEME_URLS, so that the variant it changes already exists.
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-common-settings",
        """
# Campus theme on top of Indigo's light theme (tutor-plugins/campustheme.py).
MFE_CONFIG.setdefault("PARAGON_THEME_URLS", {}).setdefault("variants", {}).setdefault(
    "light", {}
).setdefault("urls", {})["brandOverride"] = "{{ CAMPUS_THEME_PARAGON_URL }}"
""",
    ),
    priority=hooks.priorities.LOW,
)
