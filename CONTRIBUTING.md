# Cómo contribuir a DNS One

Gracias por tu interés en mejorar DNS One. Esta guía resume el flujo de trabajo
del equipo y las convenciones del repo.

---

## Flujo de trabajo

1. **Issue primero.** Antes de empezar a codear, abre o asigna un issue que
   describa el problema o la mejora.
2. **Branch desde `main`.** Convención de nombres:
   - `feat/<slug-corto>` — nueva funcionalidad
   - `fix/<slug-corto>` — corrección de bug
   - `chore/<slug-corto>` — mantenimiento / dependencias
   - `docs/<slug-corto>` — documentación
3. **Commits con mensaje claro.** Formato:
   ```
   <tipo>(<área>): resumen corto en español

   Cuerpo opcional explicando el porqué.
   ```
   Tipos: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`.
4. **Pull request a `main`.** Llena la plantilla de PR. CI debe pasar verde
   antes del merge.
5. **Code review obligatorio.** Mínimo 1 revisor.

---

## Setup local

```bash
git clone https://github.com/leonemmanuel16/dnsone.git
cd dnsone
cp .env.example .env
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed
```

---

## Convenciones de código

### Backend (Python)

- **Formato:** `ruff format`
- **Lint:** `ruff check`
- **Tipado:** type hints obligatorios en funciones públicas
- **Tests:** `pytest`. Toda lógica de negocio nueva debe tener test unitario.
- **Naming:** `snake_case` para funciones/variables, `PascalCase` para clases.

### Frontend (TypeScript / Next.js)

- **Formato:** `prettier`
- **Lint:** `eslint`
- **Naming:** `camelCase` para variables/funciones, `PascalCase` para componentes
- **Componentes:** funcionales con hooks; un componente por archivo

### General

- **Comentarios y documentación:** español
- **Identificadores en código:** inglés
- **Mensajes de log y errores de usuario:** español
- **Mensajes de error técnicos / debugging:** inglés

---

## Tests

```bash
# Unit + integration backend
docker compose exec backend pytest -v

# Cobertura
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

Cobertura mínima esperada: **80%** en `app/services/` y `app/integrations/`.

---

## Migraciones

Después de modificar un modelo SQLAlchemy:

```bash
docker compose exec backend alembic revision --autogenerate -m "descripción corta"
# revisar el archivo generado en backend/alembic/versions/
docker compose exec backend alembic upgrade head
```

---

## Reportar bugs

Abrir un issue con:

- Versión / commit
- Pasos para reproducir
- Comportamiento esperado vs. observado
- Logs relevantes (sin secretos)
- Entorno (Docker local, Ubuntu, navegador)
