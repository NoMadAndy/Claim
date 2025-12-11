# Deployment-Anleitung für Claim

## 🚀 Automatisches Deployment nach git pull

Dieses System ermöglicht ein vollständig automatisiertes Deployment: Sobald du `git push` machst, wird die Anwendung auf dem Production-Server automatisch aktualisiert und neu gestartet.

### Architektur

```
GitHub Repository
    ↓ (push)
Production Server
    ↓ (watcher checks every 60s)
Auto-Deployment Service (systemd)
    ↓
Docker Containers (rebuild & restart)
    ↓
Live-Anwendung
```

---

## 🐳 Docker-basiertes Deployment (Empfohlen)

### Anforderungen
- **Ubuntu/Debian Server** (22.04 LTS empfohlen)
- **Docker & Docker Compose** installiert
- **Git** installiert
- Internet-Zugang zu GitHub

### Automatische Setup (Einmalig)

Führe diesen Befehl auf dem Production-Server aus:

```bash
sudo bash /path/to/setup-production.sh
```

Oder mit Docker direkt:

```bash
sudo bash -c "curl https://raw.githubusercontent.com/NoMadAndy/Claim/main/tools/setup-production.sh | bash"
```

### Was wird installiert?

1. **System-Abhängigkeiten**: Docker, Git, curl
2. **Repository**: Geklont nach `/opt/claim`
3. **Auto-Deployment Watcher**: Läuft als systemd-Service
4. **Docker Compose Stack**: 
   - PostgreSQL/PostGIS Datenbank
   - FastAPI Backend
   - Automatisches Health-Check & Restart

### Konfiguration

**`.env` Datei anpassen:**

```bash
sudo nano /opt/claim/.env
```

Wichtige Variablen:
- `DB_PASSWORD`: Sicheres Datenbank-Passwort
- `CORS_ORIGINS`: Erlaubte Frontend-Domains
- `DOMAIN`: Deine Domäne (z.B. claim.example.com)

---

## 🔄 Automatisches Deployment im Betrieb

### Wie es funktioniert

1. **Du machst einen Commit und pushst zu GitHub:**
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```

2. **Der Server holt sich die Änderungen alle 60 Sekunden (konfigurierbar)**

3. **Bei neuen Commits:**
   - Code wird gepullt
   - Docker-Images werden neu gebaut
   - Container werden gestoppt und neu gestartet
   - Health-Checks werden durchgeführt
   - Alter Container werden bereinigt

### Status überwachen

```bash
# Live-Logs des Watcher-Services
sudo journalctl -u claim-watcher -f

# Service-Status
sudo systemctl status claim-watcher

# Docker Container Status
docker-compose -f /opt/claim/docker-compose.prod.yml ps

# Deployment-Logs
tail -f /opt/claim/.deploy.log
tail -f /opt/claim/.watcher.log
```

### Check-Intervall anpassen

Standard: **60 Sekunden**

In `/etc/systemd/system/claim-watcher.service`:
```ini
ExecStart=/opt/claim/tools/deploy-watcher.sh 30  # Alle 30 Sekunden
```

Dann neustarten:
```bash
sudo systemctl restart claim-watcher
```

---

## 🛠️ Manuelle Deployment-Befehle

### Deployment manuell auslösen

```bash
cd /opt/claim
bash tools/deploy.sh
```

### Container steuern

```bash
# Alle Container starten
docker-compose -f docker-compose.prod.yml up -d

# Container stoppen
docker-compose -f docker-compose.prod.yml down

# Logs anschauen
docker-compose -f docker-compose.prod.yml logs -f api

# Container neu bauen
docker-compose -f docker-compose.prod.yml build --no-cache

# Services neu starten
docker-compose -f docker-compose.prod.yml restart
```

---

## 🔐 Sicherheit & Best Practices

### Environment-Variablen schützen
```bash
chmod 600 /opt/claim/.env
```

### SSH-Keys für GitHub (optional)
Falls das Repository private ist:
```bash
sudo -u root ssh-keygen -t ed25519 -f ~/.ssh/github_claim
# Füge public key in GitHub deployment keys hinzu
```

### Firewall-Regeln
```bash
# Nur interne Ports exposiert, Reverse-Proxy davor
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (für Let's Encrypt)
sudo ufw allow 443/tcp   # HTTPS
```

### Rate Limiting für Deployments
Das System verhindert parallele Deployments automatisch. Siehe `LOCK_FILE` in `deploy.sh`.

---

## 📊 Monitoring & Logging

### Deployment-Log durchsuchen
```bash
# Letzte erfolgreiche Deployments
grep "DEPLOYMENT SUCCESSFUL" /opt/claim/.deploy.log | tail -20

# Fehler anschauen
grep "ERROR\|WARN" /opt/claim/.deploy.log

# Specific timestamp
grep "2025-12-11" /opt/claim/.deploy.log
```

### Performance-Monitoring
```bash
# Container Resource-Usage
docker stats claim-api claim-db

# Disk-Space überprüfen
df -h /opt/claim
docker system df
```

---

## ❌ Fehlerbehandlung

### Problem: Service startet nicht

```bash
# Logs überprüfen
sudo journalctl -u claim-watcher -n 50

# Service manuell testen
bash /opt/claim/tools/deploy-watcher.sh

# Service neu starten
sudo systemctl restart claim-watcher
```

### Problem: Docker build schlägt fehl

```bash
# Build-Cache löschen
docker system prune -a

# Neu bauen
docker-compose -f /opt/claim/docker-compose.prod.yml build --no-cache
```

### Problem: Datenbank-Verbindungsfehler

```bash
# Datenbank-Health überprüfen
docker-compose -f /opt/claim/docker-compose.prod.yml exec db pg_isready

# Logs der Datenbank
docker-compose -f /opt/claim/docker-compose.prod.yml logs db
```

---

## 🚨 Rollback bei Fehlern

Falls ein Deployment Fehler verursacht:

```bash
# Letzten funktionierenden Commit wiederherstellen
cd /opt/claim
git log --oneline | head -20
git reset --hard <commit-hash>

# Erneutes Deployment auslösen
bash tools/deploy.sh
```

---

## 📈 Skalierung & Optimization

### Mehrere API-Instanzen (Load-Balancing)

In `docker-compose.prod.yml`:
```yaml
api:
  deploy:
    replicas: 3  # 3 API-Container
  ports:
    - "8000-8002:8000"
```

### Postgres Performance

In `.env`:
```
DB_MAX_CONNECTIONS=100
DB_SHARED_BUFFERS=256MB
```

---

## 📝 Checkliste für Production-Setup

- [ ] Server-Zugriff und Berechtigungen
- [ ] `.env`-Datei mit sicheren Passwörtern
- [ ] Firewall-Regeln konfiguriert
- [ ] DNS / Domain-Namen konfiguriert
- [ ] Backup-Strategy für Datenbank
- [ ] Monitoring & Alerting eingerichtet
- [ ] SSL/HTTPS mit Let's Encrypt (siehe [Reverse-Proxy](#))
- [ ] Erste manuelle Deployment durchführen
- [ ] Auto-Watcher starten und testen
- [ ] Git-Hooks lokal installiert (`bash tools/setup-hooks.sh`)

---

## 🔗 Weitere Ressourcen

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [systemd Service Files](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2025-12-11
