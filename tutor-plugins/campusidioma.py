"""
Tutor plugin: every MFE in Spanish (LANGUAGE_CODE), whatever the browser's language.

1. The LMS and Studio pages already use LANGUAGE_CODE (Open edX enables Dark Lang
   on install, which only serves that language). The MFEs, though, pick their
   language from the `openedx-language-preference` cookie and, without it, from the
   browser. The LMS only sets that cookie for users with a saved language
   preference, so anonymous visitors (login, registration) and users created from
   Campus saw the MFEs in English when their browser was in English.
   This sets the cookie to LANGUAGE_CODE as soon as any MFE loads, before it
   chooses its language, on the domain the LMS uses for it (shared with the MFEs).
   The LMS then saves it as the user's preference, so emails and the LMS agree.

2. The official es-419 catalogs (openedx-translations) leave some messages empty
   (the timed/proctored exams of the learning MFE, parts of login/registration,
   Paragon components...) and break others: placeholders translated ({título} for
   {title}), plural/select keywords translated ('otro' for 'other'), Transifex HTML.
   react-intl cannot format a broken message and shows the English default instead,
   e.g. the section highlights modal in Studio. tutor-plugins/traducciones/<lang>.json
   replaces those messages after `pull_translations` (it always wins over the
   official text, so only put reviewed messages there). It also flattens Paragon's
   catalogs, which come as {"string": "..."} objects that the MFEs cannot use.

Both are compiled into the MFE image: `make update` / `make start` rebuild it in
local (build_mfe_if_changed); for dev, qa and prod bump MFE_IMAGE_TAG.
"""
import json
import os

from tutor import hooks

# Language of the platform, the same as LANGUAGE_CODE in config/tutor.env.
_LANG = "es_419"
_OVERRIDES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traducciones", f"{_LANG}.json")

with open(_OVERRIDES, encoding="utf-8") as f:
    _messages = {pkg: msgs for pkg, msgs in json.load(f).items() if not pkg.startswith("_")}

hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-env-config-buildtime-definitions",
        """
// campusidioma: force the platform language in every MFE (see tutor-plugins/campusidioma.py).
(() => {
  const name = 'openedx-language-preference';
  const lang = '{{ LANGUAGE_CODE }}';
  const current = document.cookie.split('; ').find((c) => c.startsWith(`${name}=`));
  if (current !== `${name}=${lang}`) {
    const secure = window.location.protocol === 'https:' ? '; Secure; SameSite=None' : '; SameSite=Lax';
    document.cookie = `${name}=${lang}; domain={{ LMS_HOST.split(':')[0] }}; path=/; max-age=31536000${secure}`;
  }
})();
""",
    )
)

# Runs in every MFE after `make pull_translations` (src/i18n/messages/<package>/<lang>.json).
_MERGE_JS = """
const fs = require('fs');
const path = require('path');
const lang = process.argv[2];
const overrides = JSON.parse(fs.readFileSync('/openedx/campus-i18n.json', 'utf8'));
const root = 'src/i18n/messages';
const text = (v) => (v && typeof v === 'object' ? v.string || '' : v || '');
if (fs.existsSync(root)) {
  for (const pkg of fs.readdirSync(root)) {
    const file = path.join(root, pkg, `${lang}.json`);
    if (!fs.existsSync(file)) continue;
    const messages = JSON.parse(fs.readFileSync(file, 'utf8'));
    let filled = 0;
    for (const key of Object.keys(messages)) messages[key] = text(messages[key]);
    for (const [key, value] of Object.entries(overrides[pkg] || {})) {
      if (messages[key] !== value) { messages[key] = value; filled += 1; }
    }
    fs.writeFileSync(file, JSON.stringify(messages, null, 2));
    console.log(`campusidioma: ${file} +${filled}`);
  }
}
"""

hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-dockerfile-pre-npm-build",
        "{% raw %}\n"
        + "COPY <<'CAMPUS_I18N_JSON' /openedx/campus-i18n.json\n"
        + json.dumps(_messages, ensure_ascii=False)
        + "\nCAMPUS_I18N_JSON\n"
        + f"RUN node - {_LANG} <<'CAMPUS_I18N_JS'\n"
        + _MERGE_JS.strip()
        + "\nCAMPUS_I18N_JS\n"
        + "{% endraw %}",
    )
)
