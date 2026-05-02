# Arquitectura — DNS One

> Versión: MVP · Fecha: 2026-05-01

## Vista general

DNS One es una aplicación web monolítica con dos servicios principales (backend
y frontend) más una base de datos relacional. Está diseñada para ejecutarse
con Docker Compose en cualquier servidor Linux y empaquetada para despliegue
inmediato en Ubuntu sobre Azure.

```
                                 ┌──────────────┐
                                 │   Browser    │
                                 │ (Next.js UI) │
                                 └──────┬───────┘
                                        │ HTTPS / JWT
                                        ▼
┌────────────────────┐         ┌──────────────────┐         ┌──────────────┐
│  APScheduler jobs  │  cada   │  FastAPI (API)   │  ←→     │  PostgreSQL  │
│  (cada 30 min)     │  30 min │  + SQLAlchemy    │         │              │
└────────┬───────────┘         └────────┬─────────┘         └──────────────┘
         │                              │
         │                              │ HTTPS
         ▼                              ▼
   ┌─────────────────────────────────────────┐
   │         Bind ERP (sistema externo)      │
   └─────────────────────────────────────────┘
```

## Componentes

### 1. Backend (`backend/`)
**Stack:** FastAPI 0.115 + Python 3.11 + SQLAlchemy 2 + Alembic + APScheduler + WeasyPrint.

Responsabilidades:
- Exponer API REST versionada (`/api/v1`)
- Persistir cotizaciones, clientes, productos, usuarios, logs
- Sincronizar con Bind ERP cada 30 min (productos + estatus)
- Empujar cotizaciones a Bind on-demand
- Generar PDFs de cotización
- Autenticación JWT + autorización RBAC

Estructura:
```
backend/app/
  api/v1/         → endpoints HTTP (auth, products, customers, projects, sync)
  api/deps/       → dependencias FastAPI (auth, permisos)
  core/           → settings, db, security, logging, excepciones
  models/         → ORM SQLAlchemy
  schemas/        → Pydantic (input/output)
  repositories/   → CRUD genérico (capa thin sobre Session)
  services/       → lógica de negocio (pricing)
  integrations/
    bind/         → BindClient + mapper + sync service
    syscom/       → stub para fase 2
  jobs/           → scheduler APScheduler
  pdf/            → WeasyPrint + plantilla Jinja2
  utils/          → decimal helpers, generación de códigos
  scripts/        → seed, migración asistida
```

### 2. Frontend (`frontend/`)
**Stack:** Next.js 14 (App Router) + TypeScript + Tailwind.

Responsabilidades:
- Login con JWT (almacenado en `localStorage`, fase 2 → cookies httpOnly)
- Listado y detalle de cotizaciones, productos, clientes
- Editor inline de partidas con recálculo automático
- Botón "Push a BIND" y descarga de PDF

Estructura:
```
frontend/
  app/
    login/        → /login (público)
    (app)/        → grupo de rutas protegidas (requieren token)
      projects/   → lista, nuevo, detalle
      products/
      customers/
  components/     → Sidebar, etc
  lib/            → api.ts (fetch + JWT), auth.ts (storage), types.ts
```

### 3. Base de datos
PostgreSQL 16. Migraciones gestionadas por Alembic.

**Modelos principales:**
- `users`, `roles`, `permissions`, `role_permissions` — auth + RBAC
- `customers`, `products` — entidades comerciales sincronizables con BIND
- `projects` — la cotización-proyecto (cabecera)
- `quote_items` — partidas
- `project_versions` — snapshots inmutables al pushear a BIND
- `bind_sync_logs`, `integration_events` — bitácora

Ver [`docs/bind-mapping.md`](bind-mapping.md) para el mapeo a Bind ERP.

### 4. Scheduler (APScheduler)
Corre dentro del proceso del backend (BackgroundScheduler) en lifespan de FastAPI.

Jobs:
- `bind_sync_products` — cada 30 min: trae catálogo de Bind y hace upsert
- `bind_sync_quote_status` — cada 30 min: actualiza estatus de cotizaciones enviadas

Trazabilidad: cada corrida deja registro en `bind_sync_logs`.

### 5. Integración Bind ERP
Encapsulada en `app/integrations/bind/`. Tres archivos:

| Archivo | Responsabilidad |
|---------|-----------------|
| `bind_client.py` | HTTP client (`httpx`) con retries (`tenacity`) y modo mock |
| `bind_mapper.py` | Convierte payloads BIND ↔ modelos DNS One |
| `bind_sync_service.py` | Orquesta sync de productos, estatus y push de cotizaciones |

**Modo mock:** activado con `BIND_USE_MOCK=true` en `.env`. Permite trabajar
localmente sin credenciales reales.

## Flujos clave

### Flujo 1 — Sincronización automática de productos (cada 30 min)
1. APScheduler dispara `_job_sync_products`
2. `BindClient.get_products()` trae lista
3. Por cada item: upsert por `bind_product_id`
4. Se registra `BindSyncLog` con `records_in`, `records_out`, errores

### Flujo 2 — Crear cotización + push a BIND
1. Frontend crea proyecto vía `POST /api/v1/projects` (incluye partidas)
2. Backend genera código `DNS-2026-NNNNN`, calcula totales y persiste
3. Usuario edita partidas en `/projects/[id]` (cada cambio recalcula)
4. Click en "Enviar a BIND" → `POST /api/v1/projects/{id}/push-bind`
5. `bind_sync_service.push_quote_to_bind()`:
   - Crea `IntegrationEvent` con payload
   - Llama `BindClient.create_quote()`
   - Guarda `bind_quote_id` y `bind_folio` en el proyecto
   - Crea snapshot inmutable en `project_versions`

### Flujo 3 — PDF
1. Usuario click "PDF" en detalle del proyecto
2. Frontend abre `GET /api/v1/projects/{id}/pdf` en nueva pestaña
3. Backend renderiza Jinja2 (`quote.html`) con datos del proyecto
4. WeasyPrint convierte HTML → PDF
5. Se devuelve con `Content-Disposition: inline`

## Decisiones técnicas
Ver [`docs/decisions.md`](decisions.md).

## Despliegue
Ver [`README.md`](../README.md) para desarrollo local.
Ver [`docs/ubuntu-troubleshooting.md`](ubuntu-troubleshooting.md) para producción Ubuntu.
