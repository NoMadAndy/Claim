# Claim - GPS-Spiel

Ein ortsbasiertes Echtzeit-GPS-Spiel mit FastAPI, WebSockets, PostGIS und Leaflet.

## 🎮 Spielprinzip

**Claim** ist ein standortbasiertes GPS-Spiel, bei dem Spieler:
- Spots in der echten Welt besuchen und "claimen"
- XP und Items sammeln
- Dominanz über Gebiete aufbauen (Heatmap)
- Ihre Routen tracken
- In Echtzeit mit anderen Spielern interagieren

### Features

#### Auto-Logging & Manual-Logging
- **Auto-Log**: Automatisch bei ≤20m Entfernung
- **Manual-Log**: Manuell bei ≤100m Entfernung
- **Cooldown**: 5 Minuten pro Spot
- Belohnungen: XP, Claim-Punkte, optional Items

#### Claims & Dominanz
- Claim-Werte steigen mit jedem Log
- Zeitbasierter Abfall (Decay)
- Heatmap zeigt Claim-Dichte
- Mehrere Spieler-Heatmaps gleichzeitig darstellbar

#### Tracking
- Live-Tracking ein-/ausschaltbar
- Automatische Streckenspeicherung
- Historische Tracks anzeigen
- Statistiken: Distanz, Dauer

#### Kompass & Heading
- Device Orientation API Unterstützung
- Richtungspfeil auf Spieler-Marker
- Optional: Kartenrotation nach Heading

#### Loot-Spots
- Spielerbezogene Loot-Generierung
- Temporäre Spots mit XP und Items
- Ablaufzeit (Timeout)

## 🚀 Setup & Installation

### Voraussetzungen
- Docker & Docker Compose (für Devcontainer)
- VS Code mit Dev Containers Extension
- Git

### Installation mit GitHub Codespaces

1. **Repository öffnen in Codespaces:**
   - Klicke auf "Code" → "Create codespace on main"
   - Warten bis Container erstellt wurde

2. **Datenbank initialisieren:**
   ```bash
   python app/database.py
   # oder
   python app/models.py
   ```

3. **Server starten:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Frontend aufrufen:**
   - Öffne die Port-Weiterleitung für Port 8000
   - Navigiere zu `https://your-codespace-url.github.dev`

### Lokale Installation mit Devcontainer

1. **Repository klonen:**
   ```bash
   git clone https://github.com/NoMadAndy/Claim.git
   cd Claim
   ```

2. **In VS Code öffnen:**
   ```bash
   code .
   ```

3. **Container starten:**
   - VS Code öffnet automatisch: "Reopen in Container"
   - Oder: Strg+Shift+P → "Dev Containers: Reopen in Container"

4. **Server starten** (siehe oben)

### Manuelle Installation (ohne Container)

1. **Voraussetzungen:**
   - Python 3.11+
   - PostgreSQL mit PostGIS Extension

2. **Dependencies installieren:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Umgebungsvariablen setzen (.env):**
   ```env
   DATABASE_URL=postgresql://claim_user:claim_password@localhost:5432/claim_db
   SECRET_KEY=your-secret-key-change-in-production
   ```

4. **Datenbank initialisieren:**
   ```bash
   python app/models.py
   ```

5. **Server starten:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🔧 Konfiguration

### Reverse Proxy Support

Das System ist vollständig Reverse-Proxy-kompatibel und funktioniert hinter:
- Nginx
- Traefik
- Caddy
- Apache
- GitHub Codespaces Port-Forwarding

#### Nginx Beispiel-Konfiguration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### Traefik Docker Labels:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.claim.rule=Host(`claim.yourdomain.com`)"
  - "traefik.http.services.claim.loadbalancer.server.port=8000"
```

### Spieleinstellungen (app/config.py)

```python
AUTO_LOG_DISTANCE = 20.0  # Meter für Auto-Log
MANUAL_LOG_DISTANCE = 100.0  # Meter für Manual-Log
LOG_COOLDOWN = 300  # Sekunden (5 Minuten)
CLAIM_DECAY_RATE = 0.01  # Abfall pro Stunde
```

## 📊 API Dokumentation

### REST API Endpunkte

Nach dem Start verfügbar unter:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

#### Haupt-Endpunkte:

- **Auth**: `/api/auth` - Registrierung, Login, Token
- **Spots**: `/api/spots` - Spots erstellen, abrufen, löschen
- **Logs**: `/api/logs` - Logging von Spot-Besuchen
- **Claims**: `/api/claims` - Claim-Daten, Heatmaps
- **Tracks**: `/api/tracks` - Tracking starten, beenden, Punkte hinzufügen
- **Items**: `/api/items` - Items und Inventar
- **Stats**: `/api/stats` - Spieler-Statistiken

### WebSocket Events

**Connection**: `ws://localhost:8000/ws?token=YOUR_JWT_TOKEN`

#### Client → Server Events:
```javascript
{
  "event_type": "position_update",
  "data": {
    "latitude": 51.505,
    "longitude": -0.09,
    "heading": 180
  }
}
```

#### Server → Client Events:
- `position_update` - Andere Spieler-Positionen
- `log_event` - Log-Events von Spielern
- `loot_spawn` - Loot-Spot erschienen
- `claim_update` - Claim-/Dominanz-Änderung
- `tracking_update` - Tracking-Status-Updates

## 🔄 Automatischer Repository-Sync

### Auto-Sync nutzen

Das Projekt enthält ein Skript für automatischen Git-Sync mit Changelog:

```bash
./tools/auto_sync.sh
```

Das Skript:
1. Prüft auf Änderungen
2. Fragt nach Changelog-Nachricht
3. Aktualisiert `CHANGELOG.md`
4. Committed alle Änderungen
5. Pusht zum Repository

### Manueller Changelog-Eintrag

Format in `CHANGELOG.md`:
```
2025-12-06 14:30
Kurze, präzise Beschreibung der Änderung (1 Zeile)

```

## 📱 Frontend Features

### UI-Elemente

#### Stats Bar (oben)
- Level, XP-Balken, Claim-Punkte
- Ausklappbare Details (Logs, Spots, Tracks, Inventar)

#### Karte
- OpenStreetMap, Satellite, Topo-Layer
- Spot-Marker (permanent & Loot)
- Spieler-Marker mit Heading
- Heatmap-Layer für Claims
- Track-Darstellung

#### Action Bar (unten)
- **Track**: Tracking ein/aus
- **Follow**: GPS-Follow-Modus
- **Compass**: Kompass aktivieren
- **Center**: Karte zentrieren
- **Heat**: Heatmap anzeigen
- **Layers**: Kartenlayer wechseln

### Gesten-Optimierung

- **Kein Pinch-Zoom** (verhindert versehentliches Zoomen)
- **Kein Double-Tap-Zoom**
- **Portrait-optimiert**
- Touch-Gesten für Kartennavigation

## 🗄️ Datenbankstruktur

### Tabellen

- **users** - Spieler mit Level, XP, Rolle
- **spots** - Permanente & Loot-Spots mit PostGIS Geometrie
- **logs** - Log-Einträge mit Belohnungen
- **claims** - Claim-Werte pro Spieler/Spot
- **tracks** - Gespeicherte Routen
- **track_points** - Einzelne Track-Punkte mit GPS-Daten
- **items** - Verfügbare Items
- **inventory** - Spieler-Inventar

### PostGIS Features

- `ST_Distance` - Distanzberechnung
- `ST_DWithin` - Radius-Suche
- `ST_MakeLine` - Track-Linien
- `ST_Length` - Streckenlänge
- Geography-Type für präzise Erdkugel-Berechnungen

## 🎯 Rollen & Berechtigungen

### Traveller (Standard)
- Spots loggen
- Tracks erstellen
- Items sammeln

### Creator
- Alle Traveller-Rechte
- **Spots erstellen**

### Admin
- Alle Creator-Rechte
- Spots löschen
- Systemverwaltung

## 🔮 Geplante Features (KI-Vorbereitung)

Die Architektur ist vorbereitet für:
- **KI-Loot-Spawner**: Intelligente Loot-Generierung
- **KI-Quests**: Dynamische Missionen
- **KI-NPCs**: Virtuelle Charaktere auf der Karte
- **KI-Balancing**: Adaptive Schwierigkeit

Implementierung über Services-Layer möglich ohne Core-Änderungen.

## 🛠️ Entwicklung

### Projektstruktur

```
Claim/
├── .devcontainer/          # Docker Container Config
├── app/
│   ├── routers/           # API Endpoints
│   ├── services/          # Business Logic
│   ├── ws/                # WebSocket Handler
│   ├── models.py          # SQLAlchemy Models
│   ├── schemas.py         # Pydantic Schemas
│   ├── database.py        # DB Connection
│   ├── config.py          # Settings
│   └── main.py            # FastAPI App
├── frontend/
│   ├── index.html         # UI
│   ├── styles.css         # Styling
│   └── app.js             # Logic & WebSocket
├── tools/
│   └── auto_sync.sh       # Git Auto-Sync
├── requirements.txt       # Python Dependencies
├── CHANGELOG.md           # Änderungshistorie
└── README.md             # Diese Datei
```

### Testing

```bash
# Tests ausführen (wenn implementiert)
pytest

# Linting
ruff check app/

# Type Checking
mypy app/
```

### Database Migrations (optional)

```bash
# Alembic initialisieren
alembic init migrations

# Migration erstellen
alembic revision --autogenerate -m "Initial migration"

# Migration anwenden
alembic upgrade head
```

## 🐛 Fehlerbehebung

### Datenbank-Verbindungsfehler
```bash
# PostGIS Extension manuell aktivieren
psql -U claim_user -d claim_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### WebSocket Verbindungsfehler
- Token überprüfen (JWT gültig?)
- CORS-Einstellungen prüfen
- Reverse-Proxy WebSocket-Support prüfen

### GPS funktioniert nicht
- HTTPS erforderlich (außer localhost)
- Browser-Berechtigungen prüfen
- Mobile: Standortdienste aktiviert?

## 📄 Lizenz

[Lizenz hier einfügen]

## 👥 Beiträge

Contributions willkommen! Bitte:
1. Fork erstellen
2. Feature-Branch erstellen
3. Änderungen committen mit aussagekräftigen Nachrichten
4. Pull Request erstellen

## 📞 Support

Bei Fragen oder Problemen:
- GitHub Issues erstellen
- [Kontakt-Info hier einfügen]

---

**Viel Spaß beim Claimen! 🗺️🎮**
# Test
