# Claim - GPS-Spiel

Ein ortsbasiertes Echtzeit-GPS-Spiel mit FastAPI, WebSockets, PostGIS und Leaflet.

**Aktuelle Version:** v1.2.2

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
  - Kontinuierliche Überprüfung jede Sekunde
  - Automatische Retry-Logik bei Netzwerkfehlern (bis zu 2 Wiederholungen mit exponentieller Verzögerung)
  - GPS-Genauigkeitsfilter: Nur bei Genauigkeit ≤50m
  - Verhindert doppelte Logs durch intelligente Deduplizierung
- **Manual-Log**: Manuell bei ≤100m Entfernung
- **Cooldown**: 5 Minuten pro Spot
  - Auto-Logs werden durch Auto- UND Manual-Logs blockiert
  - Manual-Logs werden nur durch andere Manual-Logs blockiert
- **Visuelle Cooldown-Anzeige**: Spots werden farbig markiert mit pulsierenden Glow-Effekten
  - 🟢 Grün mit Glow: Bereit zum Loggen (beide Log-Typen verfügbar)
  - 🟡 Gelb/Orange mit Glow: Teilweise Abklingzeit (< 2.5 Min auf irgendeinem Log-Typ)
  - 🔴 Rot mit Glow: Volle Abklingzeit (mindestens ein Log-Typ auf Cooldown)
  - **Funktioniert für Auto- UND Manual-Logs identisch** - zeigt immer den längeren der beiden Cooldowns
  - Automatische Aktualisierung alle 15 Sekunden und direkt nach jedem Log
- Belohnungen: XP, Claim-Punkte, optional Items

#### Claims & Dominanz
- Claim-Werte steigen mit jedem Log
- Zeitbasierter Abfall (Decay)
- Heatmap zeigt Claim-Dichte
- Mehrere Spieler-Heatmaps gleichzeitig darstellbar
- **Territory-Overlay mit Dominanz-Anzeige**: 
  - Hex-Tiles zeigen die Farbe des dominierenden Spielers pro Bereich
  - Automatische Berechnung der Dominanz basierend auf Claim-Punkten
- **Spot-Besitzer-Anzeige**:
  - Jeder Spot zeigt den aktuellen Besitzer (Spieler mit den meisten Claim-Punkten)
  - 👑 Crown-Icon im Popup mit Spielername in der Spielerfarbe
  - Farbiger Ring um den Spot in der Farbe des dominierenden Spielers
  - Top 3 Claimer im Detail-Bereich des Popups
  - Cooldown-Status bleibt als Spot-Farbe sichtbar (grün/gelb/rot)
  - Kombinierte Anzeige: Cooldown + Dominanz + Besitzer gleichzeitig erkennbar

#### Tracking
- Live-Tracking ein-/ausschaltbar
- Automatische Streckenspeicherung
- Historische Tracks anzeigen
- Statistiken: Distanz, Dauer
- **Smooth Player Movement**: Flüssige Spielerbewegung mit Interpolation
- **Verbesserte Trail-Effekte in Spielerfarbe**:
  - Trail verwendet individuelle Spielerfarbe (aus Heatmap-Farbe)
  - Größere Trail-Punkte (11-14px Radius) mit dynamischen Glow-Effekten in Spielerfarbe
  - Weißer Stroke-Outline für optimalen Kontrast auf allen Kartenhintergründen (OSM, Satellite, Topo)
  - Erhöhte Opazität für bessere Sichtbarkeit bei direktem Sonnenlicht
  - Schnelle Bewegungen erzeugen noch hellere Trail-Punkte mit stärkeren Effekten
  - Automatische GPS-Genauigkeitsfilterung (nur bei ≤45m Genauigkeit)
- **Optimierte Kartenfolge**: Schnellere und flüssigere Kartenanpassung im Follow-Modus

#### Kompass & Heading
- Device Orientation API Unterstützung
- Richtungspfeil auf Spieler-Marker
- Optional: Kartenrotation nach Heading

#### Loot-Spots
- Spielerbezogene Loot-Generierung
- Temporäre Spots mit XP und Items
- Ablaufzeit (Timeout)

#### Benutzereinstellungen
- **Persistente Einstellungen**: Alle Einstellungen werden pro Spieler gespeichert
- Kartenebene-Auswahl (OSM, Satellite, Topo)
- Sound- und Lautstärke-Einstellungen
- Kompass-Präferenzen
- Heatmap- und Territory-Overlay-Einstellungen
- Einstellungen werden automatisch beim nächsten Login wiederhergestellt

#### Energie-Monitoring & Optimierung 🔋
Claim bietet umfassende Funktionen zur Überwachung und Optimierung des Energieverbrauchs:

- **Batterie-Status-Anzeige**: Echtzeit-Überwachung des Batterielevels und Ladestatus
  - ⚠️ **iPhone/iOS Hinweis**: Battery Status API ist auf iOS-Geräten nicht verfügbar (Apple-Plattformbeschränkung)
  - Auf iPhone/iPad werden alternative Optimierungsoptionen angeboten
- **Verbrauchsanalyse**: Identifikation der energieintensivsten Prozesse (GPS, Netzwerk, Tracking, etc.)
- **Restlaufzeit-Schätzung**: Berechnung der geschätzten verbleibenden Akkulaufzeit basierend auf aktuellem Verbrauchsmuster
- **Energiesparmodus**: Manuell aktivierbar oder automatisch bei niedrigem Akkustand
  - Auf iPhone/iPad: Manuelle Aktivierung verfügbar (automatische Aktivierung nicht möglich ohne Battery API)
- **Intelligente Optimierungen**:
  - Reduzierte GPS-Update-Frequenz im Energiesparmodus
  - Verringerte WebSocket-Update-Rate
  - Niedrigere GPS-Genauigkeit bei kritischem Akkustand
  - Batch-Verarbeitung von Netzwerk-Anfragen
- **Optimierungsvorschläge**: Personalisierte Tipps basierend auf Nutzungsmustern
- **Konfigurierbare Schwellwerte**: Anpassbare Einstellungen für automatische Aktivierung
  - Auf iPhone/iPad: Auto-Enable-Einstellung nicht verfügbar
- **Metriken-Tracking**: Automatische Aufzeichnung des Energieverbrauchs für Analysen

**Zugriff**: Öffne die Einstellungen (⚙️) → Tab "🔋 Energy" für alle Energie-Features

**iPhone/iOS Unterstützung**: 
- ✅ Energiesparmodus (manuell)
- ✅ Verbrauchsanalyse & Optimierungsvorschläge
- ✅ Alle GPS/Netzwerk-Optimierungen
- ❌ Battery Status API (nicht verfügbar auf iOS)
- ❌ Automatische Aktivierung bei niedrigem Akkustand

#### iPhone/iOS Audio Support
Claim implementiert umfangreiche Optimierungen für zuverlässige Soundausgabe auf iPhones:

- **Audio-Unlock-Button**: Button in den Einstellungen zum Aktivieren von Sound (iOS-Anforderung)
- **Automatische Context-Wiederherstellung**: Audio wird nach App-Wechsel/Bildschirmsperre automatisch wiederhergestellt
- **Eager Sound-Preloading**: Alle Sounds werden beim ersten Unlock vorgeladen
- **State Monitoring**: Kontinuierliche Überwachung des AudioContext-Status
- **Haptic Feedback**: Vibrationen als Fallback wenn Sound deaktiviert oder nicht verfügbar ist
- **Visibility-Handler**: Reaktivierung von Audio wenn App wieder im Vordergrund ist

**Wichtige Hinweise für iPhone-Nutzer:**
- Öffne die Einstellungen (⚙️) und tippe auf den "Audio freischalten" Button um Sound zu aktivieren!
- Der Ring/Silent-Schalter am iPhone beeinflusst die Web Audio API nicht
- Sound funktioniert auch im Silent-Modus (nur Klingeltöne sind stumm)
- Nach längerer Inaktivität oder App-Wechsel einmal auf die Karte tippen um Audio zu reaktivieren
- Falls kein Sound zu hören ist: Lautstärke prüfen und ggf. den Audio-Freischalten-Button in den Einstellungen erneut drücken

## 🚀 Setup & Installation

### Voraussetzungen
- Docker & Docker Compose (für Devcontainer)
- VS Code mit Dev Containers Extension
- Git

### Installation mit GitHub Codespaces

1. **Repository öffnen in Codespaces:**
   - Klicke auf "Code" → "Create codespace on main"
   - Warten bis Container erstellt wurde

2. **Git Hooks installieren (einmalig):**
   ```bash
   bash tools/setup-hooks.sh
   ```
   Dies installiert einen pre-commit Hook, der automatisch die Version und den Timestamp bei jedem Commit aktualisiert.

3. **Datenbank initialisieren:**
   ```bash
   python app/database.py
   # oder
   python app/models.py
   ```

4. **Server starten:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Frontend aufrufen:**
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

## � Production Deployment

Das System unterstützt **vollständig automatisiertes Deployment** mit Docker:

### Quick Start (One-Liner für Ubuntu/Debian)

```bash
curl https://raw.githubusercontent.com/NoMadAndy/Claim/main/tools/setup-production.sh | sudo bash
```

### Workflow nach Setup:
1. **Lokale Änderungen machen** → `git push origin main`
2. **Server holt sich die Änderungen** automatisch alle 60 Sekunden
3. **Container werden neu gebaut** und restartet
4. **Live-Anwendung** wird sofort aktualisiert

### Status überprüfen:
```bash
# Live-Logs anschauen
sudo journalctl -u claim-watcher -f

# Container Status
docker-compose -f /opt/claim/docker-compose.prod.yml ps

# Deployment-Logs
tail -f /opt/claim/.deploy.log
```

**Vollständige Deployment-Dokumentation:** Siehe [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🔧 Konfiguration

### Reverse Proxy Support

Das System ist vollständig Reverse-Proxy-kompatibel und funktioniert hinter:
- Nginx
- Traefik
- Caddy
- Apache
- GitHub Codespaces Port-Forwarding

#### Nginx Beispiel-Konfiguration:

Siehe [nginx-config.conf](nginx-config.conf) für Production-Setup mit SSL/TLS.

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
- **Spots**: `/api/spots` - Spots erstellen, abrufen, löschen (mit Cooldown-Status)
- **Logs**: `/api/logs` - Logging von Spot-Besuchen
- **Claims**: `/api/claims` - Claim-Daten, Heatmaps
- **Tracks**: `/api/tracks` - Tracking starten, beenden, Punkte hinzufügen
- **Items**: `/api/items` - Items und Inventar
- **Stats**: `/api/stats` - Spieler-Statistiken
- **Settings**: `/api/settings` - Benutzereinstellungen laden und speichern
- **Energy**: `/api/energy` - Energie-Monitoring und Optimierungseinstellungen
  - `POST /api/energy/metrics` - Energie-Metrik aufzeichnen
  - `GET /api/energy/metrics` - Energie-Metriken abrufen
  - `POST /api/energy/stats` - Energie-Statistiken mit Optimierungsvorschlägen
  - `GET /api/energy/settings` - Energie-Einstellungen abrufen
  - `PATCH /api/energy/settings` - Energie-Einstellungen aktualisieren

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
- **Spieler-Farben-Anzeige**: 
  - Verbesserte Darstellung mit größeren Farbboxen (36x36px)
  - Weiße Rahmen und Schatteneffekte für bessere Sichtbarkeit
  - Sekundärer Farbindikator mit Glow-Effekt
  - Optimierter Kontrast für Hell- und Dunkelmodus

#### Karte
- OpenStreetMap, Satellite, Topo-Layer
- **Spot-Marker** (permanent & Loot):
  - Automatisch verborgen bei Zoom-Level < 13 für bessere Übersicht
  - Nur Hex-Tiles bleiben bei niedrigem Zoom sichtbar
- **Spieler-Marker** mit Heading und farbigem Trail
  - Trail in individueller Spielerfarbe mit dynamischen Glow-Effekten
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
- **Zugriff auf Admin Dashboard** (`/admin.html`)
  - Benutzer-, Spot- und Log-Verwaltung
  - Server Logs Einsicht mit Auto-Refresh
  - Changelog-Ansicht
  - Spieleinstellungen konfigurieren

## 🔮 Geplante Features (KI-Vorbereitung)

Die Architektur ist vorbereitet für:
- **KI-Loot-Spawner**: Intelligente Loot-Generierung
- **KI-Quests**: Dynamische Missionen
- **KI-NPCs**: Virtuelle Charaktere auf der Karte
- **KI-Balancing**: Adaptive Schwierigkeit

Implementierung über Services-Layer möglich ohne Core-Änderungen.

## 🛠️ Entwicklung

### 🧪 Lokale Entwicklung & Testing

#### Quick Start (SQLite - Ohne Docker)

Für schnelles Entwickeln und Testen ohne PostgreSQL/PostGIS:

```bash
# Install dependencies
pip install -r requirements.txt

# Use SQLite for local development
export DATABASE_URL="sqlite:///./claim_dev.db"

# Initialize database
python -m app.models

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test file
pytest tests/test_changelog.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

#### Database Options

Das System unterstützt sowohl SQLite (für Entwicklung/Tests) als auch PostgreSQL (für Production):

- **Development**: `sqlite:///./claim_dev.db` - Schnell, kein Docker benötigt
- **Testing**: `sqlite:///:memory:` - In-Memory, ultra-schnell
- **Production**: `postgresql://...` - Vollständiger PostGIS Support

**Hinweis:** SQLite unterstützt keine räumlichen PostGIS-Queries. Für volle Funktionalität nutze PostgreSQL.

#### Testing-Umgebung

Das Projekt nutzt:
- **pytest** - Test Framework
- **pytest-asyncio** - Async Test Support
- **httpx** - HTTP Client für API-Tests
- **SQLite In-Memory** - Schnelle Test-Datenbank

Alle Tests laufen automatisch mit SQLite in-memory Database für maximale Geschwindigkeit.

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

### Linting & Type Checking

```bash
# Linting (optional)
ruff check app/

# Type Checking (optional)
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

**Postgres Healthcheck Fehler "database does not exist":**
- Wenn in den Docker-Logs Fehler wie `FATAL: database "claim_user" does not exist` erscheinen, obwohl die Datenbank `claim_db` existiert, liegt das am Healthcheck.
- Der `pg_isready` Befehl prüft standardmäßig eine Datenbank mit dem gleichen Namen wie der Benutzer.
- **Lösung**: Der Healthcheck in `docker-compose.yml` muss explizit die konfigurierte Datenbank mit `-d` angeben:
  ```yaml
  test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-claim_user} -d ${DB_NAME:-claim_db}"]
  ```
- Dies verhindert die irreführenden Log-Meldungen und stellt sicher, dass die richtige Datenbank geprüft wird.

### WebSocket Verbindungsfehler
- Token überprüfen (JWT gültig?)
- CORS-Einstellungen prüfen
- Reverse-Proxy WebSocket-Support prüfen

### GPS funktioniert nicht
- HTTPS erforderlich (außer localhost)
- Browser-Berechtigungen prüfen
- Mobile: Standortdienste aktiviert?

### Auto-Log funktioniert nicht oder ist unzuverlässig

#### Häufige Ursachen und Lösungen:

1. **GPS-Genauigkeit zu niedrig**
   - Auto-Log benötigt GPS-Genauigkeit ≤50m
   - Bei schlechter GPS-Qualität wird Auto-Log automatisch pausiert
   - **Lösung**: Freie Sicht zum Himmel, GPS-Kalibrierung auf dem Gerät

2. **Cooldown noch aktiv**
   - Nach Manual-Log: 5 Min Cooldown für Auto- UND Manual-Log
   - Nach Auto-Log: 5 Min Cooldown nur für Auto-Log
   - **Prüfen**: Spot-Farbe (rot/gelb = Cooldown aktiv)

3. **Zu weit vom Spot entfernt**
   - Auto-Log aktiviert sich erst bei ≤20m Entfernung
   - **Prüfen**: Debug-Logs zeigen tatsächliche Entfernung
   - **Tipp**: Manual-Log funktioniert bis 100m

4. **Netzwerkprobleme**
   - Auto-Log verwendet automatische Retry-Logik (bis 2x)
   - Bei wiederholten Fehlern wird 5-Min-Cooldown gesetzt
   - **Debug aktivieren**: Browser-Konsole zeigt detaillierte Auto-Log-Meldungen
   - **Lösung**: Stabile Internetverbindung prüfen

5. **Debug-Modus aktivieren**
   ```javascript
   // In Browser-Konsole eingeben für detaillierte Auto-Log-Logs:
   window.debugLog = console.log.bind(console, '[DEBUG]');
   ```
   Zeigt: Trigger-Distanzen, GPS-Genauigkeit, Retry-Versuche, Cooldown-Status

#### Konfiguration (app/config.py):
```python
# Game Settings mit Pydantic Field defaults
AUTO_LOG_DISTANCE: float = Field(default=20.0)  # Meter - Radius für Auto-Log
MANUAL_LOG_DISTANCE: float = Field(default=100.0)  # Meter - Radius für Manual-Log
LOG_COOLDOWN: int = Field(default=300)  # Sekunden (5 Minuten)
```

#### Performance-Tuning (frontend/app.js):
```javascript
// Autolog retry configuration constants
const AUTO_LOG_MAX_RETRIES = 2;  // Anzahl Wiederholungen bei Fehlern
const AUTO_LOG_RETRY_DELAY_MS = 2000;  // Basisverzögerung in ms (exponentiell)
const AUTO_LOG_MAX_DELAY_MS = 10000;  // Maximale Verzögerung (Cap)

// Check-Intervall: 1 Sekunde (setInterval in initApp)
```

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

## 🏷️ Versionen & Releases

### Zurück zu einer früheren Version wechseln

```bash
# Verfügbare Versionen anzeigen
git tag

# Zu einer bestimmten Version wechseln
git checkout v1.0.0

# Zurück zur neuesten Version
git checkout main
```

### Aktuelle Version (v1.0.0)
- ✅ Auto-Login mit Retry-Logic
- ✅ Case-insensitive Login mit Enter-Key-Support
- ✅ Version & Timestamp Display (automatisch)
- ✅ Portrait-Lock für Mobile (PWA)
- ✅ Vereinfachte Heatmap (alle Player sichtbar)
- ✅ Auto-Update Heatmap nach jedem Log
- ✅ AutoLog Check jede Sekunde
- ✅ Umfassendes Debug-Logging
- ✅ Automatisches Cache-Busting
- ✅ Git Hooks für Version-Injektion

---

**Viel Spaß beim Claimen! 🗺️🎮**
