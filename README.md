# DNS One

Plataforma interna unificada de **Data Network Solutions (DNS)** que integra
**CRM + ERP + Cotizaciones** en una sola aplicación, sincronizada con
**Bind ERP** y preparada para Syscom.

> **Estado:** MVP en construcción. Ver `docs/` para arquitectura y decisiones.

---

## Características clave

- **Cotización = proyecto:** cada cotización en DNS One se modela como un
  proyecto con partidas, versiones, cliente y estado.
- **Sincronización BIND cada 30 min:** productos y estatus de cotizaciones.
- **PDF profesional descargable** por cotización.
- **Auth + RBAC:** login con JWT y permisos configurables por usuario.
- **Multi-divisa USD/MXN** con tipo de cambio configurable.
- **API REST documentada** vía OpenAPI/Swagger.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI + Python 3.11 |
| ORM | SQLAlchemy 2 + Alembic |
| DB | PostgreSQL 16 |
| Scheduler | APScheduler |
| PDF | WeasyPrint |
| Frontend | Next.js 14 (App Router) + Tailwind |
| Infra dev | Docker Compose |
| Infra prod | Ubuntu 22.04+ en Azure |

---

## Quick start (desarrollo local con Docker)

```bash
# 1. Clonar
git clone https://github.com/leonemmanuel16/dnsone.git
cd dnsone

# 2. Variables de entorno
cp .env.example .env
# editar .env y poner valores reales (JWT_SECRET_KEY, ADMIN_PASSWORD, etc.)

# 3. Levantar todo
docker compose up -d --build

# 4. Aplicar migraciones + seed inicial
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed

# 5. Listo
# Backend (Swagger):  http://localhost:8000/docs
# Frontend:           http://localhost:3000
# Health:             http://localhost:8000/health
```

Ver `docs/architecture.md` y `docs/ubuntu-troubleshooting.md` para más detalle.

---

## Estructura

```
dnsone/
├── backend/               FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── api/v1/        Endpoints versionados
│   │   ├── core/          Config, DB, security, logging
│   │   ├── models/        ORM SQLAlchemy
│   │   ├── schemas/       Pydantic
│   │   ├── repositories/  Acceso a datos
│   │   ├── services/      Lógica de negocio
│   │   ├── integrations/  BIND, Syscom
│   │   ├── jobs/          APScheduler (sync 30 min)
│   │   ├── pdf/           Plantillas + generación
│   │   └── utils/
│   ├── alembic/           Migraciones
│   └── tests/             pytest
├── frontend/              Next.js 14 + Tailwind
├── docs/                  Arquitectura, decisiones, troubleshooting
├── scripts/               setup_ubuntu.sh, start.sh, healthcheck.sh
├── .github/workflows/     CI: lint + test + build
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Comandos comunes

```bash
# Tests backend
docker compose exec backend pytest

# Lint / format
docker compose exec backend ruff check app/
docker compose exec backend ruff format app/

# Crear migración nueva (después de cambiar modelos)
docker compose exec backend alembic revision --autogenerate -m "descripción"
docker compose exec backend alembic upgrade head

# Logs
docker compose logs -f backend
docker compose logs -f frontend
```

---

## Documentación

- [`docs/architecture.md`](docs/architecture.md) — arquitectura del sistema
- [`docs/decisions.md`](docs/decisions.md) — decisiones técnicas (ADRs)
- [`docs/bind-mapping.md`](docs/bind-mapping.md) — mapeo de campos DNS One ↔ Bind ERP
- [`docs/ubuntu-troubleshooting.md`](docs/ubuntu-troubleshooting.md) — fallas comunes en Ubuntu

---

## Contribuir

Ver [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Licencia

MIT — ver [`LICENSE`](LICENSE).
