# Changelog

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

