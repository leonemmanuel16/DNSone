# Troubleshooting — Ubuntu / Producción

Errores comunes al instalar o ejecutar DNS One en Ubuntu y cómo resolverlos.

## Setup inicial

### `bash scripts/setup_ubuntu.sh` falla con "permission denied"
**Causa:** falta `sudo`.
**Solución:** `sudo bash scripts/setup_ubuntu.sh`.

### `docker: command not found` después del setup
**Causa:** la sesión actual no refrescó el `PATH`.
**Solución:** cierra sesión SSH y vuelve a entrar, o `newgrp docker`.

### `docker compose` (sin guion) no funciona
**Causa:** versión vieja con `docker-compose` standalone.
**Solución:** `sudo apt install docker-compose-plugin` o reinstala con el script.

### Permission denied al correr `docker` sin sudo
**Causa:** el usuario no está en el grupo `docker`.
**Solución:**
```bash
sudo usermod -aG docker $USER
exit  # cerrar sesión y volver a entrar
```

## Arranque de servicios

### `docker compose up` se queda colgado en Postgres
**Causa:** primera vez, Postgres está inicializando volúmenes.
**Solución:** esperar 20-30 s o `docker compose logs db` para ver progreso.

### Backend no arranca: `psycopg2.OperationalError: connection refused`
**Causa:** la DB tarda más en estar lista.
**Solución:** el `start.sh` ya tiene un loop de espera. Si ocurre fuera del script:
```bash
docker compose up -d db
sleep 5
docker compose up -d backend
```

### `alembic upgrade head` falla: `target database is not up to date`
**Causa:** se modificó la base manualmente.
**Solución:** revisar versiones aplicadas:
```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
```
Si la base está perdida, **dev only**: `make db-reset` (¡destructivo!).

## WeasyPrint / PDF

### `OSError: cannot load library libgobject-2.0.so.0`
**Causa:** faltan libs nativas que WeasyPrint requiere.
**Solución:** dentro del contenedor backend ya están. Si corres fuera de Docker:
```bash
sudo apt install -y libcairo2 libpango-1.0-0 libpangoft2-1.0-0 \
  libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info
```

### El PDF se descarga vacío o roto
**Causa:** el template Jinja2 falló silenciosamente o la letra no está disponible.
**Solución:**
```bash
docker compose exec backend python -c "
from app.models.project import Project
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.pdf.quote_pdf import render_quote_pdf
db = SessionLocal()
p = db.query(Project).first()
pdf = render_quote_pdf(p)
print(len(pdf), 'bytes')
"
```

## Scheduler / Sync con BIND

### El sync no corre cada 30 min
**Causa:** scheduler deshabilitado o backend reiniciándose.
**Solución:**
1. Ver `.env`: `SCHEDULER_ENABLED=true` y `SYNC_INTERVAL_MINUTES=30`
2. Logs: `docker compose logs backend | grep -i scheduler`
3. Disparar manualmente para validar: `POST /api/v1/sync/products`

### `BindClient` tira `IntegrationError: Bind no configurado`
**Causa:** `BIND_USE_MOCK=false` pero faltan `BIND_BASE_URL` o `BIND_API_TOKEN`.
**Solución:** rellenar el `.env` o poner `BIND_USE_MOCK=true`.

### Los productos no aparecen en la UI tras "Sync con BIND"
**Causa:** el modo mock está apagado y BIND respondió vacío.
**Solución:** revisar último log:
```bash
curl -H "Authorization: Bearer <jwt>" http://localhost:8000/api/v1/sync/logs?page_size=5
```

## Firewall / red

### El frontend no puede llamar al backend desde otro equipo
**Causa:** Postgres y backend están bindeados a `0.0.0.0` pero ufw bloquea.
**Solución:**
```bash
sudo ufw allow 80/tcp     # nginx delante (recomendado)
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp     # SSH
# NO exponer 8000 ni 5432 directo
sudo ufw enable
```

### CORS bloquea el frontend en producción
**Causa:** `CORS_ORIGINS` no incluye el dominio de Azure.
**Solución:** editar `.env`:
```
CORS_ORIGINS=https://dnsone.tudominio.com,https://www.dnsone.tudominio.com
```
y `docker compose restart backend`.

## Espacio en disco

### Postgres llenó el disco (volumen `postgres-data`)
```bash
docker system df              # ver uso de Docker
docker compose exec db psql -U dnsone -d dns_one -c "
  SELECT pg_size_pretty(pg_database_size('dns_one'));
"
```
Limpieza:
```bash
docker compose exec db vacuumdb -U dnsone -d dns_one --full --analyze
docker system prune -a --volumes  # ¡cuidado, borra también imágenes no usadas!
```

## SSL / dominio

### Subdominio Azure no resuelve a la VM
**Causa:** registro DNS no propagado o IP pública incorrecta.
**Solución:**
1. Confirmar IP pública: `curl ifconfig.me` en la VM
2. Verificar registro A en tu DNS (Cloudflare/Azure DNS)
3. `dig dnsone.tudominio.com` desde otra máquina

### `certbot` para HTTPS
Recomendado: poner **nginx + certbot** delante de los puertos 80/443 que
proxy_pass a `localhost:3000` y `localhost:8000`. Fuera del alcance del MVP,
pero documentado en fase 2.

## Reset completo (dev)

```bash
docker compose down -v       # elimina volúmenes
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed
```
