"""
Tutor plugin: Campus, the public site (Nuxt), in `tutor local` (dev, qa, prod).

- Adds the `campus-web` container, from the registry image
  (`CAMPUS_WEB_DOCKER_IMAGE`), published by Caddy at `CAMPUS_WEB_URL`.
  It reaches the LMS, Studio and the CMS inside the Docker network; the
  links it gives the browser use the public hosts.
- Uploaded videos are kept in `$(tutor config printroot)/data/campus-web/videos`.
- `tutor images build/push/pull campus-web` builds src/front-campus/Dockerfile
  and moves the image through the registry.

- The LMS home ("/") redirects to `CAMPUS_WEB_URL` and the learner dashboard
  ("/dashboard") to `CAMPUS_WEB_URL/mis-cursos`, in every environment.

In `tutor dev` Campus runs on the host with `make front`; only the
redirects apply there.
"""
import os

from tutor import hooks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

hooks.Filters.CONFIG_DEFAULTS.add_items(
    [
        # Public site of this environment (.env).
        ("CAMPUS_WEB_URL", "http://www.local.openedx.io:3000"),
        ("CAMPUS_WEB_DOCKER_IMAGE", "campus-web:latest"),
    ]
)

hooks.Filters.ENV_PATCHES.add_items(
    [
        (
            # The LMS home ("/") is Campus and its dashboard ("/dashboard") is
            # Campus' mis-cursos, in every environment (`tutor dev` has no Caddy
            # in front of the LMS). The MFEs' "Dashboard" links (user menu,
            # course exit buttons) and the post-login default all go through
            # /dashboard. Only these paths: login, APIs, OAuth and courseware
            # must keep working. 302 so browsers don't cache it.
            # The middleware lives in the settings module itself (`__name__`),
            # so it needs no code in the openedx image, only `make config`.
            "openedx-lms-common-settings",
            """
from django.http import HttpResponseRedirect as _CampusRedirect


class CampusHomeRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("GET", "HEAD"):
            if request.path in ("/", "/index.html"):
                return _CampusRedirect("{{ CAMPUS_WEB_URL }}")
            if request.path in ("/dashboard", "/dashboard/"):
                return _CampusRedirect("{{ CAMPUS_WEB_URL.rstrip('/') }}/mis-cursos")
        return self.get_response(request)


MIDDLEWARE.insert(0, __name__ + ".CampusHomeRedirectMiddleware")
""",
        ),
        (
            "local-docker-compose-prod-services",
            """
{% set scheme = "https" if ENABLE_HTTPS else "http" %}
campus-web:
  image: {{ CAMPUS_WEB_DOCKER_IMAGE }}
  restart: unless-stopped
  environment:
    # Server side, inside the network.
    NUXT_OPENEDX_LMS_URL: "http://lms:8000"
    NUXT_OPENEDX_STUDIO_URL: "http://cms:8000"
    NUXT_CAMPUS_CMS_URL: "http://campus-cms:8000"
    NUXT_ADMIN_VIDEO_BASE_URL: "{{ CAMPUS_WEB_URL }}/media/videos"
    # Links the browser follows.
    NUXT_PUBLIC_LMS_URL: "{{ scheme }}://{{ LMS_HOST }}"
    NUXT_PUBLIC_STUDIO_URL: "{{ scheme }}://{{ CMS_HOST }}"
    NUXT_PUBLIC_PROFILE_URL: "{{ scheme }}://{{ MFE_HOST }}/profile/u/"
    NUXT_PUBLIC_LEARNING_MFE_URL: "{{ scheme }}://{{ MFE_HOST }}/learning"
  volumes:
    - ../../data/campus-web/videos:/data/videos
  depends_on:
    - permissions
    - lms
    - campus-cms
""",
        ),
        # The image runs as `node` (uid 1000): it must own the videos folder.
        ("local-docker-compose-permissions-volumes", "- ../../data/campus-web:/mounts/campus-web:z"),
        ("local-docker-compose-permissions-command", "setowner 1000 /mounts/campus-web"),
        (
            "caddyfile",
            """
# Campus (public site). No upload limit: admins upload videos of up to 2 GB.
{{ CAMPUS_WEB_URL.split("://")[-1].split("/")[0].split(":")[0] }}{$default_site_port} {
    import proxy "campus-web:3000"
}
""",
        ),
    ]
)

hooks.Filters.IMAGES_BUILD.add_item(
    # An absolute path: the build context is the submodule, not Tutor's env.
    ("campus-web", os.path.join(ROOT, "src", "front-campus"), "{{ CAMPUS_WEB_DOCKER_IMAGE }}", ())
)
hooks.Filters.IMAGES_PULL.add_item(("campus-web", "{{ CAMPUS_WEB_DOCKER_IMAGE }}"))
hooks.Filters.IMAGES_PUSH.add_item(("campus-web", "{{ CAMPUS_WEB_DOCKER_IMAGE }}"))
