# Changelog

Todos los cambios relevantes de este servicio se documentan acá.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

### Changed (BREAKING)

- `POST /validate` devuelve `400/413/415` en vez de `200 {valid: false}`.
