"""
Tutor plugin: Campus, the public site (Nuxt), in `tutor local` (qa, prod).

- Adds the `campus-web` container, from the registry image
  (`CAMPUS_WEB_DOCKER_IMAGE`), published by Caddy at `CAMPUS_WEB_URL`.
  It reaches the LMS, Studio and the CMS inside the Docker network; the
  links it gives the browser use the public hosts.
- Uploaded videos are kept in `$(tutor config printroot)/data/campus-web/videos`.
- `tutor images build/push/pull campus-web` builds src/front-campus/Dockerfile
  and moves the image through the registry.

In `tutor dev` nothing changes: Campus runs on the host with `make front`.
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
    NUXT_PUBLIC_LEARNER_DASHBOARD_URL: "{{ scheme }}://{{ MFE_HOST }}/learner-dashboard/"
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
