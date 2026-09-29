# pdf-extractext-validation

Microservicio FastAPI del sistema **PDF ExtractExt** que valida PDFs antes de que
ingresen al pipeline de extracción. Aplica dos reglas de negocio del dominio
compartido:

- **Formato**: el archivo debe comenzar con el magic number `%PDF-`.
- **Tamaño**: el archivo no debe exceder `MAX_PDF_SIZE_BYTES`.

La lectura del archivo es por chunks con un tope duro de `MAX_PDF_SIZE_BYTES + 1`
bytes, así que un PDF que excede el límite se rechaza sin cargarse entero en RAM
(guarda anti-DoS).

Las reglas de negocio no viven en este repo: se obtienen del paquete compartido
[`pdf-extractext-shared`](https://github.com/videlalauti/pdf-extractext-shared),
pinneado por tag (`v1.0.0`) en `requirements.txt`.

## Endpoints

| Método | Ruta        | Descripción |
| ------ | ----------- | ----------- |
| GET    | `/health`   | Healthcheck del servicio. Responde `200`. |
| POST   | `/validate` | Recibe `multipart/form-data` con el campo `file`. |

`POST /validate` responde según el contrato REST:

| Situación | Status | Body |
| --------- | ------ | ---- |
| PDF válido | `200` | `{"valid": true, "error": null}` |
| Extensión distinta de `.pdf` | `415` | `{"detail": "..."}` |
| Sin magic number `%PDF-` / vacío / inválido | `400` | `{"detail": "..."}` |
| Excede `MAX_PDF_SIZE_BYTES` | `413` | `{"detail": "..."}` |

### Ejemplo

```bash
curl -i -F "file=@documento.pdf" http://localhost:8000/validate
```

Cada respuesta incluye el header `X-Request-Id` (el provisto por el cliente si es
válido, o uno generado) para correlacionar logs entre servicios.

## Variables de entorno

| Variable | Default | Descripción |
| -------- | ------- | ----------- |
| `MAX_PDF_SIZE_BYTES` | `10485760` | Tamaño máximo de PDF aceptado, en bytes. |
| `CORS_ORIGINS` | `http://localhost` | Orígenes permitidos, separados por coma. No admite `*` con credenciales. |
| `LOG_LEVEL` | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `PORT` | `8000` | Puerto de escucha de uvicorn. |

Ver `.env.example` para un punto de partida. La configuración se resuelve en
`settings.py` vía `pydantic-settings` (12-Factor III).

## Cómo correr

### Local (venv)

```bash
python -m venv .venv
pip install -r requirements-dev.txt
cp .env.example .env        # opcional: ajustar variables
uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

Requiere Python 3.14 (igual que la imagen del `Dockerfile`).

### Docker

```bash
docker build -t pdf-extractext-validation .
docker run -p 8000:8000 -e CORS_ORIGINS=http://localhost pdf-extractext-validation
```

La imagen arranca con `--port ${PORT:-8000}`, corre como usuario no-root y declara
un `HEALTHCHECK` contra `/health`. La base está fijada por digest
(`python:3.14-slim-bookworm@sha256:...`) para paridad dev/prod y builds reproducibles.

## Desarrollar

```bash
pip install -r requirements-dev.txt
ruff check .          # lint
pytest tests/ -v      # tests
```

El CI (`.github/workflows/ci.yml`) corre ambos en cada push y pull request.
