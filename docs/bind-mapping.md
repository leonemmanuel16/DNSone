# Mapeo de campos DNS One ↔ Bind ERP

> Estado: **MVP con mocks**. Los nombres de campo del lado BIND son
> tentativos basados en convenciones de ERPs mexicanos. Cuando recibamos la
> documentación oficial del API de Bind, actualizaremos `bind_mapper.py` y
> este doc en una sola operación.

## 1. Productos

### BIND → DNS One (incoming, sync productos)

| BIND (mock) | DNS One (`Product`) | Notas |
|-------------|---------------------|-------|
| `bind_id` | `bind_product_id` | identificador externo (string) |
| `sku` | `sku` | clave única del producto |
| `name` | `name` |  |
| `description` | `description` |  |
| `brand` | `brand` |  |
| `category` | `category` |  |
| `unit` | `unit` | "PZA", "M", "SVC", ... |
| `cost_usd` | `cost_usd` | Decimal(14,4) |
| `cost_mxn` | `cost_mxn` | opcional |
| `list_price_usd` | `list_price_usd` |  |
| `list_price_mxn` | `list_price_mxn` |  |
| `currency` | `currency_default` | "USD" o "MXN" |
| `is_active` | `is_active` | bool |

**Función:** `bind_to_product_kwargs(payload) -> dict` en `bind_mapper.py`.

### Strategy: upsert por `bind_product_id`

```python
existing = SELECT FROM products WHERE bind_product_id = :bind_id
if existing:
    UPDATE existing fields, set bind_synced_at = now()
else:
    INSERT new product, set bind_synced_at = now()
```

## 2. Clientes

> No implementado en MVP (mock devuelve lista vacía).
> Plan: mismo patrón que productos cuando llegue el API real.

| BIND | DNS One (`Customer`) |
|------|----------------------|
| `bind_id` | `bind_customer_id` |
| `code` | `code` |
| `name` | `name` |
| `tax_id` | `tax_id` (RFC) |
| `email` | `email` |
| ... | ... |

## 3. Cotización: DNS One → BIND (outgoing, push)

### Payload enviado a BIND al crear cotización

```jsonc
{
  "external_reference": "DNS-2026-00007",   // project.code
  "customer": {
    "bind_customer_id": "BND-C-12345",       // null si no está sincronizado aún
    "name": "Razón Social S.A. de C.V.",
    "tax_id": "ABC123456XYZ",
    "email": "compras@cliente.com"
  },
  "currency": "USD",                         // o "MXN"
  "exchange_rate": "19.00",                  // string para preservar precisión
  "discount_pct": "0",
  "valid_until": "2026-06-15",
  "notes": "Vigencia 30 días, instalación incluida.",
  "items": [
    {
      "bind_product_id": "BND-P-0001",       // null si es ad-hoc
      "sku": "UBQ-USW-LITE-8POE",
      "description": "Switch UniFi Lite 8 PoE",
      "qty": "2",
      "unit_price": "189.00",
      "discount_pct": "0",
      "tax_pct": "16"
    }
  ]
}
```

**Función:** `project_to_bind_quote(project) -> dict` en `bind_mapper.py`.

### Respuesta esperada de BIND

```jsonc
{
  "bind_quote_id": "BND-Q-AB12CD3456",
  "folio": "COT-X9KZ7M",
  "status": "borrador" | "enviada" | "aprobada" | ...
}
```

Estos tres campos se guardan en `projects.bind_quote_id`, `projects.bind_folio`,
`projects.bind_status` respectivamente.

## 4. Estatus de cotización: BIND → DNS One

Cada 30 min, para cada `project` con `bind_quote_id != NULL`:

```python
resp = client.get_quote_status(project.bind_quote_id)
project.bind_status = resp["status"]
project.bind_synced_at = now()
```

## 5. Bitácora

Toda llamada a BIND deja rastro:

- **`bind_sync_logs`**: una fila por corrida de sync (productos o estatus).
  Incluye `started_at`, `ended_at`, `records_in`, `records_out`,
  `errors_count`, `message`.

- **`integration_events`**: una fila por evento individual (típicamente push
  de una cotización). Guarda `payload_json`, `result_json`, `error_message`.

## 6. Cómo migrar de mock a BIND real

1. Obtener documentación del API de Bind ERP (URL base, esquema de auth, contratos).
2. Editar `.env`:
   ```
   BIND_BASE_URL=https://api.bind.com.mx/v1
   BIND_API_TOKEN=...
   BIND_USE_MOCK=false
   ```
3. Verificar que los nombres de campo en `bind_mapper.py` coinciden con el contrato real:
   - Productos: ajustar `bind_to_product_kwargs()`
   - Cotizaciones: ajustar `project_to_bind_quote()` y la lectura de `create_quote` response
4. Ajustar paths en `bind_client.py` (`/products`, `/quotes`, etc.) si BIND usa otros.
5. Probar:
   ```bash
   docker compose exec backend python -c "
   from app.integrations.bind.bind_sync_service import sync_products_from_bind
   print(sync_products_from_bind())
   "
   ```
6. Si todo OK: dejar `BIND_USE_MOCK=false` en producción.

## 7. Pendientes / TODO

- [ ] Confirmar nombres exactos de campos con doc oficial Bind
- [ ] Confirmar formato de auth (Bearer vs API key en header custom)
- [ ] Verificar si BIND devuelve paginación cursor-based o page/page_size
- [ ] Añadir endpoint para sincronizar **clientes** (no implementado en MVP)
- [ ] Manejo de productos descontinuados en BIND: ¿`is_active=false` o eliminar?
