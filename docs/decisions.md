# Decisiones técnicas (ADRs ligeras)

Cada decisión describe contexto, alternativas y razón. Si una decisión cambia,
se actualiza con el nuevo razonamiento.

---

## ADR-001 — Cotización modelada como `Project`

**Contexto:** El requisito de negocio dice "cada cotización = proyecto".

**Decisión:** Una sola tabla `projects` cumple el doble rol. Un proyecto puede
permanecer en estado `draft` indefinidamente y ser editado, o convertirse en
`sent`/`approved`/`converted` cuando avanza el ciclo comercial.

**Alternativas descartadas:**
- Dos tablas separadas (`projects` y `quotes`): duplicación innecesaria en MVP.
- Un sistema de estados externo (workflow engine): sobre-ingeniería para 6 estados.

---

## ADR-002 — Multi-divisa USD/MXN con conversión por proyecto

**Contexto:** DNS opera con proveedores en USD y clientes mexicanos. El TC USD/MXN cambia diariamente.

**Decisión:**
- Default del proyecto: **USD** (la mayoría de proveedores facturan así)
- Campo `currency` por proyecto + `exchange_rate` (default 19.00, configurable)
- Productos guardan precio/costo en ambas monedas (`*_usd`, `*_mxn`) para evitar conversión repetida
- El usuario decide por proyecto si quiere cotizar en USD o MXN

**Alternativas descartadas:**
- Conversión automática por API externa (Banxico): añade dependencia, deferimos a fase 2.
- Una sola moneda canónica: no refleja la operación real.

---

## ADR-003 — Cálculo de impuestos por línea con descuento global proporcional

**Contexto:** El IVA en México se cobra sobre lo que el cliente realmente paga.

**Decisión:** El descuento global se aplica proporcionalmente a cada línea
**antes** de calcular el IVA de esa línea. Esto da:
1. Subtotal venta = Σ(qty × precio × (1 − desc_línea/100))
2. Descuento global = subtotal_venta × (desc_global/100)
3. Base imponible = subtotal − descuento global
4. IVA = Σ(línea_después_del_global × tax_pct/100) — preserva tasas mixtas
5. Total = base_imponible + IVA

**Margen:** se calcula sobre la base imponible (subtotal − descuento global),
no sobre el subtotal bruto. Refleja la rentabilidad real.

**Implementación:** módulo puro `app/services/pricing.py`, testeado con `pytest`.

---

## ADR-004 — Auth con JWT + RBAC en DB (vs OIDC externo)

**Contexto:** El usuario pidió "acceso configurable por usuario".

**Decisión:** Implementar JWT firmado HS256 + tabla `roles` + tabla `permissions`
con asociación many-to-many. El usuario tiene un rol; el rol tiene N permisos.

**Permisos discretos** (ej. `projects.push_bind`, `sync.run`) que se verifican
en endpoints con dependencia `require_permission(code)`.

**Alternativas descartadas para MVP:**
- OIDC externo (Auth0, Keycloak): añade infra y costo, no requerido en MVP
- Permisos solo a nivel de rol sin granularidad: limita la capacidad de configurar accesos

**Plan futuro:** evaluar migración a cookies httpOnly (vs localStorage) y SSO
contra el AD de DNS si lo hay.

---

## ADR-005 — APScheduler in-process (vs Celery)

**Contexto:** Necesitamos correr 2 jobs cada 30 min (sync productos + estatus).

**Decisión:** APScheduler `BackgroundScheduler` dentro del proceso FastAPI.

**Pros:**
- 0 servicios extra (sin broker, sin worker)
- Suficiente para 2 jobs ligeros cada 30 min
- Logs y errores quedan junto con los del API

**Contras y mitigaciones:**
- Si hay múltiples instancias del backend, hay race condition → mitigación: en
  producción, **ejecutar solo 1 réplica del backend** o desactivar scheduler en
  réplicas y dejar 1 nodo con `SCHEDULER_ENABLED=true`
- Trabajo pesado bloquearía workers HTTP → no es el caso (jobs cortos)

**Plan futuro:** migrar a Celery + Redis si añadimos jobs largos o necesitamos
escalabilidad horizontal.

---

## ADR-006 — Modo mock de BIND como ciudadano de primera clase

**Contexto:** No tenemos credenciales BIND al iniciar. El equipo quiere
desarrollar el flujo completo igual.

**Decisión:** `BindClient` tiene un flag `BIND_USE_MOCK` que cambia entre HTTP
real y datos hardcoded en `_mock_data.py`. Los mocks devuelven payloads con la
forma esperada del API real.

**Beneficios:**
- Frontend y backend desarrollables sin credenciales
- Tests E2E manuales sin tocar BIND productivo
- Switch a real con un solo cambio de env var

**Riesgo:** los mocks pueden divergir del contrato real. **Mitigación:** cuando
tengamos doc oficial de Bind, regenerar los mocks desde un fixture del API real.

---

## ADR-007 — WeasyPrint para PDF (vs ReportLab / wkhtmltopdf)

**Contexto:** Necesitamos PDF profesional con diseño tabular y branding.

**Decisión:** WeasyPrint (HTML/CSS → PDF).

**Pros:**
- Plantilla en HTML/Jinja2: fácil de iterar
- CSS print bien soportado (`@page`, page numbers)
- Estable y mantenido

**Contras:**
- Requiere libs de sistema (cairo, pango) → ya incluidas en el Dockerfile
- Más pesado que ReportLab

**Plantilla actual:** `app/pdf/templates/quote.html` — diseño genérico
profesional. Pendiente: igualar al PDF actual de Bind ERP cuando recibamos
una muestra.

---

## ADR-008 — Frontend con localStorage para JWT (provisional)

**Decisión MVP:** JWT en `localStorage`. Simple, funciona, suficiente para MVP
interno con HTTPS.

**Plan fase 2:** migrar a cookies `httpOnly; Secure; SameSite=Lax` (más seguras
contra XSS) — requiere endpoints `/auth/login` que setean cookie y un proxy
del frontend para mantener same-origin.

---

## Pendientes de decisión

- **Backups de Postgres:** estrategia para producción Azure (snapshot diario? pg_dump cron?)
- **Logs estructurados (JSON):** evaluar `structlog` para integrarse con Azure Log Analytics
- **Rate limiting** del API (slowapi o reverse proxy)
- **Gestor de secretos en producción** (Azure Key Vault vs `.env` en el host)
