# Contrato de `POST /validate`

Servicio `pdf-extractext-validation`. Recibe un PDF por `multipart/form-data`
en el campo `file` y responde `200` o un error `4xx` según las reglas del
dominio compartido (`pdf-extractext-shared`).

## Request

| Campo | Tipo | Requerido | Descripción |
| ----- | ---- | --------- | ----------- |
| `file` | archivo | sí | PDF a validar. El nombre debe terminar en `.pdf` (sin distinguir mayúsculas). |

```bash
curl -i -F "file=@documento.pdf" http://localhost:8000/validate
```

## Respuestas

| Caso | Status | Body |
| ---- | ------ | ---- |
| PDF válido | `200` | `{"valid": true, "error": null}` |
| Extensión distinta de `.pdf` | `415` | `{"detail": "El archivo debe tener extensión .pdf"}` |
| Excede `MAX_PDF_SIZE_BYTES` | `413` | `{"detail": "El archivo excede el tamaño máximo de <bytes> bytes"}` |
| Archivo vacío | `400` | `{"detail": "El archivo está vacío"}` |
| Sin magic number `%PDF-` | `400` | `{"detail": "El archivo no tiene un formato PDF válido"}` |

El cuerpo de error sigue el formato estándar de FastAPI: `{"detail": "..."}`.

### Orden de las validaciones

1. Extensión del nombre → `415`.
2. Tamaño real mientras se lee por chunks → `413`.
3. Contenido: vacío → `400`; sin magic number `%PDF-` → `400`.

El límite se lee de `MAX_PDF_SIZE_BYTES` (default `10485760`). La lectura es por
chunks de 64 KiB, así que un archivo que excede el límite se corta sin cargarse
entero en memoria (protección anti-DoS).

## Cambio rompiente respecto del monolito

El prototipo respondía siempre `200` e indicaba el error en el body:

| Antes (monolito) | Ahora |
| ---------------- | ----- |
| `200 {"valid": false, "error": "..."}` | `400/413/415 {"detail": "..."}` |
| `200 {"valid": true, "error": null}` | `200 {"valid": true, "error": null}` |

Consecuencias para los clientes:

- Un cliente que solo miraba `valid` ahora tiene que mirar el status HTTP.
- Un cliente que trataba cualquier `2xx` como éxito debe manejar `4xx`.
- El campo `error` ya no viaja en los errores: el mensaje está en `detail`.
- `200` queda reservado exclusivamente para PDFs válidos.

### Cómo adaptar un cliente

1. Considerar válido solo `200` (y `body.valid is True`).
2. Mapear `4xx` a rechazo usando `body.detail`:
   - `415`: el archivo no es un `.pdf`; error del cliente, no reintentar.
   - `413`: el archivo supera el límite; error del cliente, no reintentar.
   - `400`: el contenido no es un PDF válido; error del cliente, no reintentar.
3. `5xx` sigue siendo un fallo del servicio: reintentar con backoff.
4. Propagar `X-Request-Id` para correlacionar logs entre servicios.

Ejemplo con `httpx`:

```python
import httpx

response = httpx.post(
    "http://validation:8000/validate",
    files={"file": ("documento.pdf", data, "application/pdf")},
)

if response.status_code == 200:
    resultado = response.json()
    assert resultado["valid"] is True
elif response.status_code in (400, 413, 415):
    raise ValueError(response.json()["detail"])
else:
    response.raise_for_status()
```

## Observabilidad

Toda respuesta incluye `X-Request-Id`: se reutiliza el valor enviado por el
cliente (si es válido) o se genera uno nuevo. El mismo id aparece en los logs
del servicio.
