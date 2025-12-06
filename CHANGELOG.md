# Changelog

## 2025-12-06 04:51:41
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:51:35
**Files:** 1filechanged,10insertions(+),1deletion(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:51:28
**Files:** 1filechanged,22insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:49:22
**Files:** 2fileschanged,9insertions(+)
**Modified:**
- `app/routers/__pycache__/tracks.cpython-312.pyc`
- `app/routers/tracks.py`

## 2025-12-06 04:44:00
**Files:** 1filechanged,1deletion(-)
**Modified:**
- `README.md`

## 2025-12-06 04:42:30
**Files:** 11fileschanged,646insertions(+),74deletions(-)
**Modified:**
- `README.md`
- `app/__pycache__/main.cpython-312.pyc`
- `app/services/__pycache__/auth_service.cpython-312.pyc`
- `app/services/__pycache__/log_service.cpython-312.pyc`
- `app/services/__pycache__/spot_service.cpython-312.pyc`
- `app/services/__pycache__/tracking_service.cpython-312.pyc`
- `app/ws/__pycache__/handlers.cpython-312.pyc`
- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`
- `tools/auto_sync.sh`

2025-12-06 02:52
Init

## 2025-12-06 16:00
Komplette Implementierung des Claim GPS-Spiels gemäß Prompt.md

### Backend
- FastAPI Backend mit allen Routers (auth, spots, logs, claims, tracks, items)
- SQLAlchemy Models mit PostGIS-Integration
- Pydantic Schemas für Request/Response-Validierung
- Services-Layer für Business-Logik
- WebSocket-Support für Echtzeit-Events
- JWT-Authentifizierung
- Reverse-Proxy-Unterstützung

### Frontend
- Leaflet-Karte mit Multi-Layer-Support (OSM, Satellite, Topo)
- GPS-Tracking mit Auto-Follow
- Device Orientation API für Kompass
- WebSocket-Client für Live-Updates
- Responsive UI mit Stats-Bar und Action-Bar
- Pinch-/Double-Tap-Zoom deaktiviert
- Benachrichtigungssystem

### Features
- Auto-Log bei ≤20m, Manual-Log bei ≤100m
- 5-Minuten Cooldown pro Spot
- Claim-System mit Decay
- Heatmap-Darstellung
- Track-Aufzeichnung mit LineString
- Loot-Spots mit Ablaufzeit
- Items & Inventar-System

### DevOps
- Devcontainer mit PostgreSQL+PostGIS
- Docker Compose Setup
- Auto-Sync-Skript für Git
- Umfangreiche README mit Setup-Anleitung

