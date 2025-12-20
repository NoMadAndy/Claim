# Changelog

## Version 1.2.4 - 2025-12-20
**Deployment & Operations Improvements**

### Fehlerbehebungen
- **Verbesserte Fehlerdiagnose im Auto-Deployment Watcher**: 
  - Git fetch Fehler werden jetzt vollständig geloggt statt unterdrückt
  - Exit-Codes werden angezeigt zur schnelleren Problemidentifikation
  - Diagnostik für fehlende Remote-Konfiguration
  - Bessere Behandlung von fehlenden initialen Commits
  - Erleichtert Troubleshooting bei Deployment-Problemen erheblich

### Technische Details
- `tools/deploy-watcher.sh`: Entfernt `2>/dev/null` von git fetch, fügt detailliertes Error-Logging hinzu
- Fehler werden jetzt mit Exit-Code, Fehlermeldung und Diagnose-Information geloggt
- Hilft Administratoren, Netzwerk- und Git-Konfigurationsprobleme schneller zu identifizieren

## Version 1.2.3 - 2025-12-16
**Heatmap Zoom-Stabilität**

### Fehlerbehebungen
- **Heatmap bleibt bei Zoom stabil**: 
  - Behebt Problem, bei dem Heatmap beim Zoomen "nachgezogen" wurde
  - Entfernt `maxZoom` Option aus Heatmap-Layern (verhindert zoom-basierte Intensitätsskalierung)
  - Heatmap-Darstellung bleibt jetzt während Zoom-Operationen visuell stabil
  - Player marker und Spots waren bereits korrekt konfiguriert

### Technische Details
- Entfernt `maxZoom: 17` aus primärem Heatmap-Layer
- Entfernt `maxZoom: 17` aus Edge-Glow Heatmap-Layer
- Leaflet.heat verwendet jetzt automatisch die maximale Zoom-Stufe der Karte

## Version 1.2.2 - 2025-12-15
**UI/UX Improvements & iPhone Compatibility**

### Neue Features
- **Changelog immer aktuell**: Settings-Changelog wird jetzt bei jedem Öffnen neu geladen statt gecacht
  - Zeigt immer die neuesten Änderungen
  - Entfernt changelogLoaded-Flag, das Updates verhinderte
- **iPhone/iOS Energy Settings Unterstützung**: 
  - Automatische Erkennung von iPhone/iPad-Geräten
  - Hinweis über Battery API-Einschränkungen auf iOS
  - Ausblenden nicht unterstützter Funktionen (Battery Status, Auto-Enable-Level)
  - Energie-Optimierungen bleiben verfügbar
- **Verbesserte Player-Farben in Stats-Anzeige**:
  - Größere Farbboxen (36x36px statt 30x30px) mit weißen Rahmen
  - Schatteneffekte für bessere Sichtbarkeit
  - Sekundärer Farbindikator mit Glow-Effekt
  - Besserer Kontrast durch Hintergrund-Highlights
- **Player-Trail in Spielerfarbe**: 
  - Trail-Dots verwenden jetzt die individuelle Spielerfarbe
  - Dynamische Glow-Effekte basierend auf Spielerfarbe
  - Weiße Stroke-Outline für Kontrast auf allen Hintergründen
- **Zoom-basierte Spot-Sichtbarkeit**:
  - Spots werden automatisch unter Zoom-Level 13 ausgeblendet
  - Nur Hex-Tiles bleiben bei niedrigem Zoom sichtbar
  - Konfigurierbarer Schwellenwert (SPOT_MIN_ZOOM_LEVEL)
  - Bessere Performance und Übersichtlichkeit bei großer Kartenansicht

### Technische Details
- iPhone-Erkennung via UserAgent und maxTouchPoints (iPad auf iOS 13+)
- CSS currentColor für dynamische Trail-Farben
- updateSpotVisibility() Funktion für Zoom-basierte Marker-Kontrolle
- Entfernt: changelogLoaded-Flag und unnötige Initialisierungs-Aufrufe

### Wichtige Dateien
- `frontend/app.js` - Changelog-Fix, Trail-Farben, Spot-Zoom, Player-Colors-UI
- `frontend/energy-monitor.js` - iPhone-Erkennung, UI-Anpassungen
- `frontend/styles.css` - Trail-CSS mit dynamischen Farben

## Version 1.2.1 - 2025-12-14
**Dominance Display & Player Recognition Enhancements**

### Neue Features
- **Hex-Tiles zeigen dominanten Spieler**: Territory-Overlay zeigt nun die Farbe des Spielers mit der größten Dominanz in jedem Hex-Bereich
  - Jeder Hex wird separat berechnet und zeigt die Farbe des führenden Spielers
  - Mehrere Spieler-Heatmaps werden gleichzeitig verarbeitet
- **Spot-Markierungen mit Dominanz-Indikator**: Spots zeigen zusätzlich einen farbigen Ring, der den dominierenden Spieler anzeigt
  - Cooldown-Status (grün/gelb/rot) bleibt sichtbar als Spot-Farbe
  - Dominanz wird als zusätzlicher Ring um den Spot dargestellt
  - Kombiniert visuelle Informationen: Cooldown + Dominanz gleichzeitig erkennbar
- **Verbesserte Settings-Ladung**: Robustere Fehlerbehandlung beim Laden von Benutzereinstellungen
  - Zusätzliche Null-Checks für soundManager
  - Bessere Fehler-Logs für Debugging

### API-Änderungen
- Erweiterung des `SpotResponse` Schemas um `dominant_player_color` Feld
- `/api/spots/nearby` Endpoint liefert jetzt dominant_player_color für jeden Spot
- Backend berechnet automatisch den dominierenden Spieler basierend auf claim_value

### Technische Details
- `cachedTerritoryHeatmap` → `cachedTerritoryHeatmaps` (Array statt einzelnes Objekt)
- `updateTerritoryOverlay()` berechnet nun Dominanz pro Hex über alle Spieler
- Neue CSS-Klassen für Spots mit Dominanz-Indikator
- CSS Custom Properties (`--dominant-color`) für dynamische Farbanpassung

## Version 1.2.0 - 2025-12-14
**Major Feature Release: Comprehensive UX & Gameplay Improvements**

### Zusammenfassung der neuen Features
Dieses Release bündelt alle wichtigen Verbesserungen der letzten Wochen in einer stabilen Version und markiert einen signifikanten Fortschritt in Spielerlebnis, Benutzerfreundlichkeit und technischer Stabilität.

### Highlights

#### 🎨 Visuelle Verbesserungen
- **Deutlich sichtbarere Player-Trails**: Trail-Punkte größer (8→10/6→8px) mit stärkeren Glow-Effekten
- **Farbige Glow-Effekte für Spots**: Pulsierende Animationen basierend auf Cooldown-Status
  - 🟢 Grün-Glow: Bereit zum Loggen (pulse-ready)
  - 🟡 Orange-Glow: Teilweise Abklingzeit (pulse-partial)
  - 🔴 Rot-Glow: Volle Abklingzeit (pulse-cooldown)
- **Flüssigere Kartenfolge**: Optimierte panTo-Animation (0.7s→0.4s)

#### 🎮 Gameplay-Erweiterungen
- **Smooth Player Movement**: Flüssige Spielerbewegung mit 800ms Ease-Out-Interpolation
- **Spots-Cooldown-Färbung**: Grün/Gelb/Rot-Markierung abhängig von Abklingzeit
- **Automatische Spot-Aktualisierung**: 15-Sekunden-Intervall + sofort nach jedem Log
- **Loot-Spots System**: Temporäre, sammelbare Spots mit XP/Items
- **Verbesserte Logging-Mechanik**: Zuverlässigeres Auto- und Manual-Logging

#### 💾 Persistente Benutzereinstellungen
- Alle Einstellungen werden pro Spieler in der Datenbank gespeichert
- Kartenebene-Auswahl wird automatisch wiederhergestellt
- Sound- und Kompass-Einstellungen persistent
- Heatmap- und Territory-Overlay-Einstellungen pro Benutzer

#### 🔊 iPhone/iOS Audio-Unterstützung
- Audio-Unlock-Button in Einstellungen
- Automatische Context-Wiederherstellung nach App-Wechsel
- Eager Sound-Preloading
- Haptic Feedback als Fallback
- Umfassende State Monitoring

#### 🎛️ Admin-Dashboard-Verbesserungen
- Server Logs Ansicht mit Auto-Refresh
- Changelog-Tab für einfachen Zugriff
- Verbesserte Lesbarkeit mit schwarzer Schriftfarbe

#### 🗺️ Multi-User-Heatmap
- Gleichzeitige Anzeige mehrerer Spieler-Heatmaps
- UI-Toggles für einfache Steuerung

### Technische Änderungen
- Neue `UserSettings` Datenbanktabelle
- API-Endpunkte: `GET/PUT /api/settings`
- `cooldown_status` in Spots-API (ready/partial/cooldown)
- CSS-Klassen: `spot-marker-ready`, `spot-marker-partial`, `spot-marker-cooldown`
- Optimierte Trail-Animationen und Drop-Shadow-Filter
- Neue Spot-Glow-CSS-Animationen (@keyframes)

### Wichtige Dateien
- `app/models.py` - UserSettings Model
- `app/routers/settings.py` - Settings API
- `app/routers/spots.py` - Cooldown-Status-Integration
- `app/routers/loot.py` - Loot-Spots Backend
- `app/services/loot_service.py` - Loot-Logik
- `frontend/app.js` - Hauptlogik für alle Features
- `frontend/styles.css` - Visuelle Verbesserungen
- `frontend/admin.html` - Admin-Dashboard-Updates

---

## 2025-12-13 Visual & UX Enhancements: Trail, Spot Glow & Map Following
**Highlights:**
- ✨ **Deutlich sichtbarere Player-Trails**: Trail-Punkte sind nun größer (8→10/6→8px) mit stärkeren Glow-Effekten und höherer Opazität für bessere Sichtbarkeit
- 🌟 **Farbige Glow-Effekte für Spots**: Spots haben jetzt pulsierende Glow-Effekte basierend auf ihrer Abklingzeit
  - 🟢 Grün-Glow: Bereit zum Loggen (pulse-ready Animation)
  - 🟡 Orange-Glow: Teilweise Abklingzeit (pulse-partial Animation)
  - 🔴 Rot-Glow: Volle Abklingzeit (pulse-cooldown Animation)
- 🔄 **Automatische Spot-Aktualisierung**: Spots werden alle 15 Sekunden automatisch aktualisiert und direkt nach jedem Log (auto/manual)
- 🗺️ **Flüssigere Kartenfolge**: Karte folgt dem Spieler nun schneller und geschmeidiger (0.7s→0.4s Dauer, optimierte Easing)
**Technische Details:**
- Trail-Dots: Erhöhte Größe, Opazität (0.4/0.5) und verbesserte Drop-Shadow-Filter
- Spot-Marker: Neue CSS-Animationen für pulsierende Glow-Effekte bei allen Cooldown-Zuständen
- Spot-Refresh-Intervall: 15 Sekunden periodisch + sofort nach jedem Log
- Map panTo: Reduzierte Dauer (0.4s) und optimierte easeLinearity (0.15) für flüssigere Bewegung
**Wichtige Dateien:**
- `frontend/app.js` - Trail-Parameter, Spot-Refresh-Intervall, panTo-Optimierung
- `frontend/styles.css` - Trail-Effekte, Spot-Glow-Animationen

## 2025-12-13 Major Feature Release: Enhanced Gameplay & User Experience
**Highlights:**
- 🎨 Spots werden jetzt abhängig von ihrer Abklingzeit eingefärbt (Grün=bereit, Gelb=teilweise, Rot=Abklingzeit)
- 🏃 Spielerbewegung ist jetzt weich und flüssig mit Interpolation statt abrupten Sprüngen
- ✨ Verbesserter Spieler-Trail-Effekt mit deutlich sichtbareren und animierten Punkten
- 🔧 Popup-Zittern beim Verschieben der Karte behoben
- 💾 Alle Benutzereinstellungen werden jetzt pro Spieler in der Datenbank gespeichert
- 🗺️ Kartenebene-Auswahl wird automatisch gespeichert und beim nächsten Login wiederhergestellt
- 🔊 Sound- und Kompass-Einstellungen werden persistent gespeichert
- 📊 Heatmap- und Territory-Overlay-Einstellungen werden pro Benutzer gespeichert
**Technische Details:**
- Neue `UserSettings` Datenbanktabelle für persistente Benutzereinstellungen
- API-Endpunkte hinzugefügt: `GET/PUT /api/settings`
- Spots-API gibt jetzt `cooldown_status` zurück (ready/partial/cooldown)
- Spieler-Marker verwendet jetzt 800ms Ease-Out-Interpolation für sanfte Bewegungen
- Trail-Dots haben verbesserte Animationen und erhöhte Sichtbarkeit
- CSS-Klassen hinzugefügt: `spot-marker-ready`, `spot-marker-partial`, `spot-marker-cooldown`
**Wichtige Dateien:**
- `app/models.py` - UserSettings Model
- `app/routers/settings.py` - Settings API (neu)
- `app/routers/spots.py` - Cooldown-Status-Integration
- `app/schemas.py` - UserSettings Schemas
- `frontend/app.js` - Smooth Movement, Settings-Speicherung, Cooldown-Farben
- `frontend/styles.css` - Cooldown-Farben, verbesserte Trail-Animationen

## 2025-12-13 UI Improvements: Changelog Readability & Admin Server Logs
**Highlights:**
- Verbesserte Changelog-Lesbarkeit: Schwarze Schriftfarbe für bessere Lesbarkeit
- Admin Dashboard: Neue Server Logs Ansicht mit Auto-Refresh Funktion
- Admin Dashboard: Changelog-Tab für einfachen Zugriff auf Änderungshistorie
- Server Logs API: Zeigt "Not created yet" Nachricht wenn Log-Datei noch nicht existiert
**Wichtige Dateien:**
- `frontend/styles.css` - Changelog-Styling auf schwarze Schrift geändert
- `frontend/admin.html` - Server Logs und Changelog Tabs hinzugefügt
- `app/routers/server_logs.py` - Backend für Server Logs (bereits vorhanden)
- `app/routers/changelog.py` - Backend für Changelog (bereits vorhanden)

## 2025-12-10 22:22:32
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/services/__pycache__/log_service.cpython-312.pyc`

## 2025-12-10 22:12:05
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/services/__pycache__/log_service.cpython-312.pyc`

## 2025-12-10 21:48:00
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`

## 2025-12-10 21:47:26
**Files:** 1filechanged,15deletions(-)
**Modified:**
- `.env.example`

## 2025-12-10 21:18:36
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-10 21:15:29
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-10 21:10:41
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-10 21:06:43
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-10 20:45:46
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`

## 2025-12-10 20:45:34
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-10 20:03:43
**Files:** 4fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`
- `app/__pycache__/schemas.cpython-312.pyc`
- `app/services/__pycache__/auth_service.cpython-312.pyc`
- `app/services/__pycache__/claim_service.cpython-312.pyc`

## 2025-12-10 19:53:23
**Files:** 3fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`
- `app/ws/__pycache__/connection_manager.cpython-312.pyc`
- `app/ws/__pycache__/handlers.cpython-312.pyc`

## 2025-12-09 22:06:02
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/schemas.cpython-312.pyc`
- `app/services/__pycache__/item_service.cpython-312.pyc`

## 2025-12-09 Feature Release: Loot Spots & Logging
**Highlights:**
- Neue Loot-Spots: Temporäre, sammelbare Spots mit XP/Items, serverseitig generiert
- Verbesserte Logging-Mechanik: Zuverlässigeres Auto- und Manual-Logging, Cooldown-Handling, Feedback
- Multi-User-Heatmap: Gleichzeitige Anzeige mehrerer Spieler-Heatmaps, UI-Toggles
- Diverse Bugfixes und UI-Verbesserungen
**Wichtige Dateien:**
- `frontend/app.js`, `frontend/index.html`, Backend: `app/routers/loot.py`, `app/routers/logs.py`, `app/services/loot_service.py`, `app/services/log_service.py`

## 2025-12-09 18:24:01
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`
- `app/ws/__pycache__/handlers.cpython-312.pyc`

## 2025-12-09 18:13:01
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-08 18:43:14
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/logs.cpython-312.pyc`

## 2025-12-08 18:25:22
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/logs.cpython-312.pyc`

## 2025-12-08 17:05:20
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`
- `app/routers/__pycache__/tracks.cpython-312.pyc`

## 2025-12-08 16:57:52
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`
- `app/routers/__pycache__/tracks.cpython-312.pyc`

## 2025-12-08 16:17:14
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`
- `app/routers/__pycache__/tracks.cpython-312.pyc`

## 2025-12-08 01:19:21
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-08 00:33:55
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/services/__pycache__/auth_service.cpython-312.pyc`

## 2025-12-07 23:50:39
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-07 23:33:43
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/items.cpython-312.pyc`

## 2025-12-07 23:26:44
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/items.cpython-312.pyc`

## 2025-12-07 23:24:00
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/items.cpython-312.pyc`

## 2025-12-07 23:01:36
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/schemas.cpython-312.pyc`
- `app/routers/__pycache__/items.cpython-312.pyc`

## 2025-12-07 22:39:42
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-07 22:38:26
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/services/__pycache__/item_service.cpython-312.pyc`
- `init_items.py`

## 2025-12-07 22:13:16
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/database.cpython-312.pyc`

## 2025-12-07 22:06:25
**Files:** 3fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/database.cpython-312.pyc`
- `app/services/__pycache__/log_service.cpython-312.pyc`
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-07 04:07:55
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`

## 2025-12-07 04:03:15
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`

## 2025-12-07 03:57:37
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`

## 2025-12-07 03:55:57
**Files:** 3fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/config.cpython-312.pyc`
- `app/__pycache__/database.cpython-312.pyc`
- `app/__pycache__/models.cpython-312.pyc`

## 2025-12-07 03:31:29
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-07 03:27:22
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-07 03:21:06
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/logs.cpython-312.pyc`
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-07 03:16:31
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/schemas.cpython-312.pyc`
- `app/routers/__pycache__/logs.cpython-312.pyc`

## 2025-12-07 03:12:29
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-07 03:04:22
**Files:** 3fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/logs.cpython-312.pyc`
- `app/services/__pycache__/log_service.cpython-312.pyc`
- `app/services/__pycache__/spot_service.cpython-312.pyc`

## 2025-12-07 02:56:14
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/logs.cpython-312.pyc`

## 2025-12-07 02:46:34
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/schemas.cpython-312.pyc`
- `app/routers/__pycache__/logs.cpython-312.pyc`

## 2025-12-07 01:30:29
**Files:** 2fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/config.cpython-312.pyc`
- `app/__pycache__/database.cpython-312.pyc`

## 2025-12-07 01:18:15
**Files:** 3fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/models.cpython-312.pyc`
- `app/routers/__pycache__/logs.cpython-312.pyc`
- `app/services/__pycache__/log_service.cpython-312.pyc`

## 2025-12-07 01:17:19
**Files:** 3fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`
- `app/__pycache__/models.cpython-312.pyc`
- `app/__pycache__/schemas.cpython-312.pyc`

## 2025-12-07 01:13:31
**Files:** 5fileschanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`
- `app/__pycache__/models.cpython-312.pyc`
- `app/__pycache__/schemas.cpython-312.pyc`
- `app/routers/__pycache__/logs.cpython-312.pyc`
- `app/services/__pycache__/log_service.cpython-312.pyc`

## 2025-12-07 01:08:18
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`

## 2025-12-07 01:05:04
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/spots.cpython-312.pyc`

## 2025-12-07 00:41:47
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-07 00:33:14
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-07 00:29:36
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-07 00:25:09
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`

## 2025-12-07 00:24:20
**Files:** 3fileschanged,14insertions(+),5deletions(-)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`
- `frontend/index.html`

<<<<<<< HEAD
## 2025-12-07 00:24:00
**Files:** 2fileschanged,15insertions(+)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`

<<<<<<< HEAD
## 2025-12-07 00:23:50
**Files:** 2fileschanged,9insertions(+),1deletion(-)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`

<<<<<<< HEAD
## 2025-12-07 00:23:39
**Files:** 3fileschanged,14insertions(+),5deletions(-)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`
- `frontend/index.html`

<<<<<<< HEAD
## 2025-12-07 00:23:29
**Files:** 2fileschanged,23insertions(+),4deletions(-)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`

<<<<<<< HEAD
## 2025-12-07 00:23:18
**Files:** 3fileschanged,14insertions(+),5deletions(-)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`
- `frontend/index.html`

<<<<<<< HEAD
## 2025-12-07 00:23:08
**Files:** 2fileschanged,19insertions(+),3deletions(-)
**Modified:**
- `CHANGELOG.md`
- `app/main.py`

<<<<<<< HEAD
## 2025-12-07 00:22:57
**Files:** 2fileschanged,42insertions(+)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`

<<<<<<< HEAD
## 2025-12-07 00:22:47
**Files:** 3fileschanged,9insertions(+),12deletions(-)
**Modified:**
- `CHANGELOG.md`
- `frontend/app.js`
- `frontend/sounds/Sound LD Bumpy Reconstruction_keyC#min.wav`

<<<<<<< HEAD
## 2025-12-07 00:11:32
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`
=======
=======
=======
=======
=======
=======
=======
=======
=======
## 2025-12-07 00:22:16
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

>>>>>>> 7271e10 (2025-12-07 00:22:16: app.js, index.html)
## 2025-12-07 00:22:05
**Files:** 1filechanged,7insertions(+)
**Modified:**
- `frontend/app.js`

>>>>>>> c1a7b29 (2025-12-07 00:22:05: app.js)
## 2025-12-07 00:21:54
**Files:** 1filechanged,1insertion(+),1deletion(-)
**Modified:**
- `frontend/app.js`

>>>>>>> 2a87549 (2025-12-07 00:21:54: app.js)
## 2025-12-07 00:20:13
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

>>>>>>> 8af569a (2025-12-07 00:20:13: app.js, index.html)
## 2025-12-07 00:20:02
**Files:** 1filechanged,15insertions(+),4deletions(-)
**Modified:**
- `frontend/app.js`

>>>>>>> 34ed795 (2025-12-07 00:20:02: app.js)
## 2025-12-07 00:15:20
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

>>>>>>> 45a9eff (2025-12-07 00:15:20: app.js, index.html)
## 2025-12-07 00:15:09
**Files:** 1filechanged,11insertions(+),3deletions(-)
**Modified:**
- `app/main.py`

>>>>>>> 25fbacb (2025-12-07 00:15:09: main.py)
## 2025-12-07 00:14:58
**Files:** 1filechanged,34insertions(+)
**Modified:**
- `frontend/app.js`

>>>>>>> d480c43 (2025-12-07 00:14:58: app.js)
## 2025-12-07 00:14:47
**Files:** 1filechanged,2insertions(+),12deletions(-)
**Modified:**
- `frontend/app.js`
>>>>>>> 152b8e2 (2025-12-07 00:14:47: app.js)

## 2025-12-07 00:09:05
**Files:** 1filechanged,16insertions(+)
**Modified:**
- `app/main.py`

## 2025-12-07 00:04:23
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-07 00:04:12
**Files:** 1filechanged,9insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-07 00:02:40
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-07 00:02:29
**Files:** 1filechanged,2insertions(+),1deletion(-)
**Modified:**
- `frontend/app.js`

## 2025-12-07 00:00:58
**Files:** 2fileschanged,6insertions(+),6deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-07 00:00:46
**Files:** 1filechanged,37insertions(+),17deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:48:43
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:48:31
**Files:** 1filechanged,29insertions(+),4deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:48:20
**Files:** 1filechanged,29insertions(+),21deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:43:48
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:43:37
**Files:** 1filechanged,1insertion(+),19deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:41:15
**Files:** 1filechanged,3insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 23:41:04
**Files:** 1filechanged,1insertion(+)
**Modified:**
- `frontend/index.html`

## 2025-12-06 23:37:22
**Files:** 2fileschanged,19insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:37:01
**Files:** 1filechanged,3insertions(+),26deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:36:50
**Files:** 1filechanged,28insertions(+),31deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:31:18
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:31:07
**Files:** 1filechanged,36insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:28:55
**Files:** 2fileschanged,31insertions(+),3deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:20:43
**Files:** 1filechanged,1insertion(+),1deletion(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 23:20:31
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 23:19:30
**Files:** 1filechanged,9insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:17:18
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:17:07
**Files:** 1filechanged,53insertions(+),29deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:14:15
**Files:** 2fileschanged,10insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:13:44
**Files:** 1filechanged,36insertions(+),7deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 23:09:12
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 23:09:00
**Files:** 1filechanged,14insertions(+),9deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:49:37
**Files:** 2fileschanged,23insertions(+),8deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:48:15
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:48:04
**Files:** 1filechanged,5insertions(+),10deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 22:47:52
**Files:** 1filechanged,2insertions(+),4deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:47:41
**Files:** 1filechanged,10insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 22:44:00
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:42:18
**Files:** 2fileschanged,6insertions(+),13deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:40:16
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:40:05
**Files:** 1filechanged,38insertions(+),51deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:38:13
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:38:02
**Files:** 1filechanged,14insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:36:41
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:36:29
**Files:** 1filechanged,29insertions(+),77deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:34:08
**Files:** 2fileschanged,5insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:33:57
**Files:** 1filechanged,9insertions(+),15deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:31:45
**Files:** 2fileschanged,7insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 22:31:34
**Files:** 1filechanged,5insertions(+)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:30:03
**Files:** 1filechanged,2insertions(+),3deletions(-)
**Modified:**
- `CHANGELOG.md`

## 2025-12-06 22:29:20
**Files:** 1filechanged,1insertion(+),7deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:26:49
**Files:** 2fileschanged,10insertions(+),4deletions(-)
**Modified:**
- `CHANGELOG.md`
- `app/main.py`

<<<<<<< HEAD
## 2025-12-06 22:18:27
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/__pycache__/main.cpython-312.pyc`
=======
## 2025-12-06 22:22:57
**Files:** 1filechanged,3insertions(+),4deletions(-)
**Modified:**
- `app/main.py`
>>>>>>> 3b0a43e (2025-12-06 22:22:57: main.py)

## 2025-12-06 22:17:35
**Files:** 1filechanged,6insertions(+)
**Modified:**
- `CHANGELOG.md`

## 2025-12-06 22:17:24
**Files:** 2fileschanged,17insertions(+)
**Modified:**
- `CHANGELOG.md`
- `app/main.py`

## 2025-12-06 22:15:51
**Files:** 1filechanged,12insertions(+)
**Modified:**
- `app/main.py`

## 2025-12-06 22:15:40
**Files:** 1filechanged,1insertion(+)
**Modified:**
- `app/main.py`

## 2025-12-06 22:10:39
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 22:10:28
**Files:** 1filechanged,35insertions(+),35deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:10:17
**Files:** 1filechanged,8insertions(+),2deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:04:35
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 22:04:23
**Files:** 1filechanged,40insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 22:04:12
**Files:** 1filechanged,11insertions(+)
**Modified:**
- `app/main.py`

## 2025-12-06 22:00:40
**Files:** 2fileschanged,23insertions(+),15deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 21:55:18
**Files:** 2fileschanged,4insertions(+),4deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 21:55:07
**Files:** 1filechanged,39insertions(+),19deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:50:05
**Files:** 2fileschanged,4insertions(+),4deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 21:49:54
**Files:** 1filechanged,26insertions(+),8deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:43:32
**Files:** 1filechanged,6insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:42:50
**Files:** 1filechanged,2insertions(+),1deletion(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:41:19
**Files:** 1filechanged,7insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:39:18
**Files:** 1filechanged,54insertions(+),61deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:39:06
**Files:** 1filechanged,3insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:35:45
**Files:** 2fileschanged,3insertions(+),1deletion(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 21:35:33
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:34:02
**Files:** 1filechanged,3insertions(+),17deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:33:51
**Files:** 1filechanged,5insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:30:59
**Files:** 1filechanged,3insertions(+),12deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:27:37
**Files:** 1filechanged,44insertions(+),31deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:24:56
**Files:** 1filechanged,48insertions(+),30deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:24:45
**Files:** 1filechanged,1insertion(+),1deletion(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:24:33
**Files:** 1filechanged,11insertions(+),4deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:20:01
**Files:** 1filechanged,4insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:17:50
**Files:** 1filechanged,22insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:14:08
**Files:** 1filechanged,19insertions(+),18deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:11:27
**Files:** 1filechanged,4insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:11:16
**Files:** 1filechanged,8insertions(+),3deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:08:14
**Files:** 1filechanged,58insertions(+)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:08:03
**Files:** 1filechanged,29insertions(+),20deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 21:06:41
**Files:** 1filechanged,64insertions(+)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:06:30
**Files:** 1filechanged,1insertion(+),106deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 21:02:28
**Files:** 1filechanged,64insertions(+),47deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:59:57
**Files:** 1filechanged,2insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:56:43
**Files:** 1filechanged,31insertions(+)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:56:32
**Files:** 1filechanged,13insertions(+),7deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:56:21
**Files:** 1filechanged,34insertions(+),8deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:56:09
**Files:** 1filechanged,5insertions(+),6deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:55:58
**Files:** 
**Modified:**

## 2025-12-06 20:53:57
**Files:** 1filechanged,6insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:53:45
**Files:** 
**Modified:**

## 2025-12-06 20:53:34
**Files:** 1filechanged,11insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:53:23
**Files:** 1filechanged,2insertions(+),1deletion(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:50:31
**Files:** 1filechanged,1insertion(+),1deletion(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:48:50
**Files:** 1filechanged,3insertions(+),3deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:37:57
**Files:** 2fileschanged,19insertions(+),21deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 20:36:16
**Files:** 1filechanged,2insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:36:04
**Files:** 1filechanged,16insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 20:34:33
**Files:** 1filechanged,36insertions(+),25deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:32:51
**Files:** 1filechanged,17insertions(+),12deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:30:20
**Files:** 1filechanged,9insertions(+),9deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:27:38
**Files:** 1filechanged,34insertions(+),9deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 20:23:47
**Files:** 2fileschanged,59insertions(+),3deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 19:47:56
**Files:** 1filechanged,39insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 19:45:28
**Files:** 2fileschanged,2insertions(+),11deletions(-)
**Modified:**
- `app/main.py`
- `frontend/index.html`

## 2025-12-06 19:42:47
**Files:** 2fileschanged,26insertions(+),6deletions(-)
**Modified:**
- `app/main.py`
- `frontend/index.html`

## 2025-12-06 19:40:48
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/index.html`

## 2025-12-06 19:38:47
**Files:** 1filechanged,24insertions(+),6deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 19:35:06
**Files:** 3fileschanged,29insertions(+),13deletions(-)
**Modified:**
- `app/routers/logs.py`
- `app/services/spot_service.py`
- `frontend/app.js`

## 2025-12-06 19:32:45
**Files:** 1filechanged,10insertions(+),4deletions(-)
**Modified:**
- `app/services/spot_service.py`

## 2025-12-06 19:28:40
**Files:** 3fileschanged,165insertions(+),5deletions(-)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`
- `frontend/styles.css`

## 2025-12-06 19:09:50
**Files:** 1filechanged,6insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 19:07:18
**Files:** 1filechanged,8insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 19:05:46
**Files:** 1filechanged,10insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 19:05:25
**Files:** 1filechanged,31insertions(+),9deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 19:03:34
**Files:** 1filechanged,1deletion(-)
**Modified:**
- `README.md`

## 2025-12-06 19:03:13
**Files:** 1filechanged,1insertion(+)
**Modified:**
- `README.md`

## 2025-12-06 19:00:41
**Files:** 1filechanged,36insertions(+),23deletions(-)
**Modified:**
- `tools/git-watch.sh`

## 2025-12-06 18:58:30
**Files:** 1filechanged,105insertions(+),73deletions(-)
**Modified:**
- `tools/auto_sync.sh`

## 2025-12-06 18:55:03
**Files:** 1filechanged,1deletion(-)
**Modified:**
- `README.md`

## 2025-12-06 18:54:03
**Files:** 
**Modified:**

## 2025-12-06 18:50:37
**Files:** 1filechanged,1insertion(+)
**Modified:**
- `README.md`

## 2025-12-06 18:44:14
**Files:** 1filechanged,1insertion(+),1deletion(-)
**Modified:**
- `tools/git-watch.sh`

## 2025-12-06 18:42:14
**Files:** 
**Modified:**

## 2025-12-06 15:17:28
**Files:** 1filechanged,2insertions(+),2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 15:06:57
**Files:** 1filechanged,2deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 15:03:59
**Files:** 2fileschanged,38insertions(+)
**Modified:**
- `frontend/app.js`
- `frontend/index.html`

## 2025-12-06 14:54:13
**Files:** 1filechanged,2insertions(+),14deletions(-)
**Modified:**
- `start.sh`

## 2025-12-06 14:52:00
**Files:** 1filechanged,24insertions(+),19deletions(-)
**Modified:**
- `start.sh`

## 2025-12-06 14:50:59
**Files:** 1filechanged,18insertions(+),3deletions(-)
**Modified:**
- `start.sh`

## 2025-12-06 14:47:56
**Files:** 1filechanged,3insertions(+),3deletions(-)
**Modified:**
- `start.sh`

## 2025-12-06 14:23:39
**Files:** 1filechanged,10insertions(+),1deletion(-)
**Modified:**
- `start.sh`

## 2025-12-06 14:19:23
**Files:** 1filechanged,13insertions(+),2deletions(-)
**Modified:**
- `start.sh`

## 2025-12-06 14:18:05
**Files:** 1filechanged,6insertions(+),4deletions(-)
**Modified:**
- `start.sh`

## 2025-12-06 04:57:00
**Files:** 1filechanged,3insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:56:53
**Files:** 1filechanged,6insertions(+)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:55:37
**Files:** 2fileschanged,4insertions(+),6deletions(-)
**Modified:**
- `app/routers/__pycache__/tracks.cpython-312.pyc`
- `app/routers/tracks.py`

## 2025-12-06 04:55:05
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/tracks.cpython-312.pyc`

## 2025-12-06 04:54:59
**Files:** 1filechanged,9insertions(+),7deletions(-)
**Modified:**
- `app/routers/tracks.py`

## 2025-12-06 04:54:27
**Files:** 1filechanged,9insertions(+),10deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:53:45
**Files:** 1filechanged,14insertions(+),8deletions(-)
**Modified:**
- `frontend/app.js`

## 2025-12-06 04:52:43
**Files:** 1filechanged,0insertions(+),0deletions(-)
**Modified:**
- `app/routers/__pycache__/tracks.cpython-312.pyc`

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

