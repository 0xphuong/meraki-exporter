# Changelog

All notable changes documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) | [Semantic Versioning](https://semver.org)

## [Unreleased]

## [1.1.0] - 2026-04-26

### Security
- **Removed phone-home tracking**: `check_env_key()` was sending `MERAKI_API_KEY` in plaintext to a hardcoded external webhook on every startup. Removed entirely.

### Added
- `/healthz` endpoint for Docker HEALTHCHECK and readiness probes
- `requirements.txt` with pinned versions
- `docker-compose.yml` for local development
- `.env.example` — template for required environment variables
- `.gitignore` — prevents `.env` from being committed
- GitHub Actions CI: lint (ruff) + Docker build test
- GitHub Actions docker-publish: build & push to Docker Hub on tag

### Changed
- Dockerfile: removed pyinstaller, now runs Python directly — simpler, smaller, faster builds
- Dockerfile: upgraded base image to `python:3.11-slim`
- Dockerfile: added `HEALTHCHECK` instruction
- `Content-Type` header on `/metrics` now includes proper Prometheus version
- Startup validation: exits with error if `MERAKI_API_KEY` or `SERIAL_*` not set
- Code cleanup: removed commented-out `print()` statements, simplified logic

## [1.0.0] - initial

### Added
- Fetch `perfScore` from Meraki appliance API
- Expose as `meraki_performance` Prometheus gauge
- Google Chat alerts: exceeded / reminder / resolved
- Multi-device support via `SERIAL_*` env vars
