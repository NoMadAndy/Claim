# Master-Prompt: Claim – GPS-Spiel mit **FastAPI**, **WebSockets**, **PostGIS** & **Leaflet** in GitHub Codespaces

Erzeuge ein vollständiges, lauffähiges Softwareprojekt für das GPS-Spiel **„Claim“** mit folgender Architektur:

- **Backend:** FastAPI (Python, ASGI)
- **Frontend:** Web-App (HTML/CSS/JavaScript) mit **Leaflet**
- **Datenbank:** PostgreSQL mit **PostGIS**
- **Echtzeit:** WebSockets
- **Reverse-Proxy-kompatibel** (jede Domain, jeder Subpfad)
- **GitHub Codespaces-kompatibel** (inkl. Devcontainer)
- **Automatischer Repository-Sync + komprimierter Changelog-Eintrag nach jeder Änderung**
- Moderne, motivierende und langfristig erweiterbare Spielmechanik

Bitte liefere **alle Dateien vollständig**, sauber strukturiert, inkl. README & Setup.

---

## 1. Grundidee & Spielprinzip

**Claim** ist ein ortsbasiertes Echtwelt-GPS-Spiel:

- Live-GPS-Position auf der Karte
- Permanente Spots
- Spielerbezogene Loot-Spots
- Claim-/Dominanz-Heatmap
- Sammelmechaniken:
  - XP
  - Items
  - Claims / Dominanzpunkte

**Ziele:**  
Kontrolle über Spots, Aufbau der eigenen Claim-Heatmap, Wettbewerb gegen andere Spieler.

---

## 2. Technische Architektur

### Backend: FastAPI

Implementiere folgende Funktionen:

- User-Registrierung & Login (JWT)
- Rollen: Traveller, Creator, Admin
- REST-API unter `/api/...` für:
  - User & Rollen
  - Spots (permanent & Loot)
  - Logs (inkl. Distanzlogik & Cooldown)
  - Claims / Dominanz
  - Heatmap-Daten
  - Tracking (live & historische Tracks)
  - Items / Inventar
- WebSockets unter `/ws/...` für:
  - Live-Positionen
  - Log-Events
  - Loot-Funde
  - Claim-/Dominanz-Updates
  - Tracking-Updates
  - System-/PvP-Events

**Datenbank:**

- PostgreSQL + PostGIS
- Tabellen:
  - users, roles
  - spots
  - logs
  - claims
  - tracks
  - items, inventory
- Nutzung von PostGIS:
  - Distanzberechnung
  - Clustering
  - Heatmap-Berechnungen
  - räumliche Filter im Kartenausschnitt

**Struktur:**

- `app/main.py`
- `app/routers/`
- `app/models/`
- `app/schemas/`
- `app/services/`
- `app/ws/`
- optional: Alembic-Migrationen

---

## Frontend: Leaflet Web-App

**Dateien:**

- `frontend/index.html`
- `frontend/styles.css`
- `frontend/app.js`

**Funktionen:**

- GPS-Position ermitteln
- Karte mit Leaflet:
  - OSM-Basiskarte
  - Luftbilder
  - Topomap
  - Marker für Spots
  - Heatmap-Layer
  - Track-Layer
- UI:
  - Stats oben
  - Buttons unten
  - Smooth-Follow der Spielerposition
- **Gestenbeschränkung:**
  - Kein Pinch-Zoom
  - Kein Double-Tap-Zoom
- **Portrait-Optimierung** (Meta & CSS)

Kommunikation über:

- REST (API)
- WebSockets (Live)

---

## 3. Reverse-Proxy-Kompatibilität

System muss funktionieren unter:

- beliebigen Domains & Subdomains
- Subpfaden (z. B. `/claim/`)
- TLS-Offloading (Nginx, Traefik, Caddy, Apache)

Anforderungen:

- Keine hartkodierten URLs im Frontend
- Konfigurierbare oder relative API-/WS-Basis-URL
- Nutzung von Forwarded-Headern:
  - `X-Forwarded-For`
  - `X-Forwarded-Proto`
  - `X-Forwarded-Host`

Namespaces:

- REST: `/api/...`
- WS: `/ws/...`

---

## 4. GitHub Codespaces, Repo-Sync & CHANGELOG

### Devcontainer

`.devcontainer/` muss enthalten:

- Python 3.x
- FastAPI-Abhängigkeiten
- PostgreSQL-Client
- Optional Docker & docker-compose
- Portfreigaben (z. B. 8000)
- Startbefehle (DB + Uvicorn)

### Automatischer Repository-Sync

Erstelle Skript `tools/auto_sync.sh`

### Kompakter Changelog nach jeder Änderung

Datei: `CHANGELOG.md`

Format:

YYYY-MM-DD
kurze, präzise Änderung (1 Zeile)

makefile
Code kopieren

Beispiel:

2025-12-06
Auto-Log bei 20m implementiert

Claim-Heatmap Layer ergänzt

### README

README soll erklären:

- wie der Changelog gepflegt wird,
- wie Auto-Sync funktioniert,
- wie man manuell Einträge ergänzen kann.

---

## 5. Gameplay-Mechaniken

### Logging (Auto & Manuell)

- **Auto-Log bei ≤ 20 m**
- **Manual Log bei ≤ 100 m**
- **5-Minuten-Cooldown pro Spot**
- Log-Effekte:
  - XP
  - Claim-/Dominanzpunkte
  - optional Fotos
  - Animation + Sound
  - UI-Feedback („+XP, +Claim“)

### Claims / Dominanz

- Werte steigen durch Logs
- Zeitbasierter Abfall (Decay)
- Heatmap zeigt Claim-Dichte eines Spielers
- Farben je Spieler
- Mehrere Heatmaps gleichzeitig einblendbar

### Tracking

- Tracking ein-/ausschaltbar
- Live-Track speichern & darstellen
- Historische Tracks anzeigen
- leichte Claim-Boni entlang der Strecke

### Kompass / Heading

- Button löst Device Orientation API aus
- Spieler-Marker zeigt echten Richtungspfeil
- optional Kartenrotation nach Heading

### Loot-Spots

- lokal pro Spieler generiert
- XP + Items
- verschwinden nach Einsammeln oder Timeout
- UI: Animation + Sound

### Mini-Games bei Stillstand

- kleine Web-Minispiele
- Belohnung: XP, Items, Skills
- Skills verbessern:
  - XP-Gewinn
  - Log-Reichweiten
  - Loot-Chancen

---

## 6. UI/UX-Struktur

### Stats oben

- Level
- XP-Balken
- Claim-Fortschritt
- ausklappbare Details

### Action-Bar unten

Buttons für:

- Tracking an/aus
- GPS-Follow
- Kompass
- Center
- Spot-Erstellung (Creator/Admin)
- Heatmap an/aus
- Live-Track an/aus
- Historische Tracks an/aus

### WebSocket-Popups

Für:

- Logs
- Loot
- Claim-Änderungen
- PvP-Hinweise
- System-Events

---

## 7. Motivation & Progression

### Kurzfristig
- XP
- Items
- Sofortfeedback (Animation & Sound)

### Mittelfristig
- Levelsystem
- Inventar
- Skills/Perks

### Langfristig
- Regionskontrolle über Claims
- Ausbau der Heatmap
- Leaderboards

---

## 8. KI-Vorbereitung

Struktur so aufbauen, dass folgende KI-Features leicht ergänzt werden können:

- KI-Loot-Spawner
- KI-Quests & Missionen
- KI-NPCs auf der Karte
- KI-Balancing (Loot, XP, Claims)

Saubere Trennung:

- Services
- Router
- ORM
- WebSocket-Events

---

## 9. Erwartete Ausgabe

Erstelle:

1. komplettes **FastAPI Backend**
2. komplettes **Leaflet Web-Frontend**
3. **PostGIS Datenbankschema** + optional Migrationen
4. vollständige **WebSocket-Event-Dokumentation**
5. **Devcontainer** + optional **docker-compose**
6. **README** mit:
   - Setup
   - Codespaces-Nutzung
   - Reverse Proxy Anleitung
   - Auto-Sync
   - Changelog-Pflege
7. Icons & Marker
8. Erweiterungsvorschläge

---

## 10. Ziel

Ein sofort startbares Projekt **Claim**, das:

- hinter jedem Reverse Proxy läuft
- dynamische API-/WS-URLs nutzt
- mobil optimiert (Portrait) ist
- Pinch-/Double-Tap-Zoom deaktiviert
- Heading-/Kompasspfeil besitzt
- Live- & Historien-Tracks zeigt
- Auto-/Manual-Logik (20 m / 100 m) besitzt
- Claim-/Dominanz-Heatmaps anzeigt
- Echtzeitkommunikation via WebSockets nutzt
- vollständig in GitHub Codespaces entwickelt wird
- nach jeder Änderung automatisch synchronisiert wird
- und einen **kompakten, gepflegten Changelog** enthält

---

**PROMPT ENDE**
