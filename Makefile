# Comandos del equipo. Escribe `make` para ver la lista.
# El ambiente lo dice .env (copia de .env.local, .env.dev, .env.qa o .env.prod).
.DEFAULT_GOAL := help
SHELL := /bin/bash

help: ## Muestra esta ayuda
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

setup: ## Instala todo desde cero en una máquina nueva
	@scripts/setup.sh

update: ## Trae los cambios del equipo (git pull) y los aplica
	@scripts/update.sh

start: ## Enciende la plataforma
	@source scripts/common.sh && "$$TUTOR" $$MODE start -d

stop: ## Apaga la plataforma
	@source scripts/common.sh && "$$TUTOR" $$MODE stop

restart: ## Reinicia el LMS, Studio y el CMS (tras cambiar código montado)
	@source scripts/common.sh && "$$TUTOR" $$MODE restart lms cms campus-cms $$([ $$MODE = local ] && echo campus-web)

logs: ## Muestra los logs del LMS
	@source scripts/common.sh && "$$TUTOR" $$MODE logs -f --tail=100 lms

cms-logs: ## Muestra los logs del CMS (campus-cms)
	@source scripts/common.sh && "$$TUTOR" $$MODE logs -f --tail=100 campus-cms

web-logs: ## Muestra los logs de Campus en dev/qa/prod (en local salen en la terminal de make front)
	@source scripts/common.sh && "$$TUTOR" $$MODE logs -f --tail=100 campus-web

contador: ## Da el rol Contador (acceso a /admin): make contador USER_NAME=usuario [REMOVE=1]
	@source scripts/common.sh && "$$TUTOR" $$MODE exec campus-cms python manage.py contador $(or $(USER_NAME),$(error Falta USER_NAME=usuario)) $(if $(REMOVE),--remove)

reconcile: ## Reintenta accesos fallidos y cierra pagos sin webhook (en el servidor, una vez al día con cron)
	@source scripts/common.sh && "$$TUTOR" $$MODE exec -T campus-cms python manage.py reconcile_orders

shell: ## Abre una consola de Django en el LMS
	@source scripts/common.sh && "$$TUTOR" $$MODE run lms ./manage.py lms shell

admin: ## Crea un superusuario: make admin USER_NAME=admin EMAIL=tu@correo.com
	@source scripts/common.sh && "$$TUTOR" $$MODE do createuser --staff --superuser $(or $(USER_NAME),admin) $(or $(EMAIL),admin@local.openedx.io)

tutor: ## Ejecuta cualquier comando de Tutor de este proyecto: make tutor ARGS="config printvalue LMS_HOST"
	@source scripts/common.sh && "$$TUTOR" $(ARGS)

backup: ## Respalda usuarios, cursos, el CMS y los videos en backups/
	@scripts/backup.sh

restore: ## Restaura un respaldo: make restore BACKUP=backups/...
	@scripts/restore.sh "$(BACKUP)"

doctor: ## Muestra versiones y estado para comparar con el equipo
	@scripts/doctor.sh

config: ## Aplica cambios de config/tutor.env o .env y reinicia lo necesario
	@scripts/config.sh

front: ## Levanta el sitio público (Nuxt) en http://www.local.openedx.io:3000
	@scripts/front.sh

stripe: ## Reenvía los webhooks de prueba de Stripe al CMS local
	@scripts/stripe.sh

build: ## [tu máquina, con .env de dev, qa o prod] Construye las imágenes y las sube al registro
	@scripts/build.sh

deploy: ## [servidor] Baja el código y las imágenes, y enciende/actualiza todo con tutor local
	@scripts/deploy.sh

