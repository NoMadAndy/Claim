# 🚀 Deployment Quick Start

**Ziel:** Nach jedem `git push` wird die Anwendung automatisch auf dem Server aktualisiert.

## ⚡ Automatisches Setup (3 Befehle)

### Auf dem Production-Server:

```bash
# 1. Als root einloggen oder sudo verwenden
sudo su

# 2. Setup-Skript herunterladen und ausführen
curl https://raw.githubusercontent.com/NoMadAndy/Claim/main/tools/setup-production.sh | bash

# 3. .env Datei konfigurieren
nano /opt/claim/.env
```

**Fertig!** Der Server prüft jetzt alle 60 Sekunden auf neue Commits und deployert automatisch.

---

## 🔄 Im Betrieb

### Code pushen (triggert Deployment):
```bash
git add .
git commit -m "Update feature"
git push origin main
```

### Status überprüfen:
```bash
# Live-Logs
sudo journalctl -u claim-watcher -f

# Container Status
docker ps
```

---

## 🛠️ Wichtige Befehle

| Befehl | Aktion |
|--------|--------|
| `sudo systemctl status claim-watcher` | Service-Status |
| `sudo journalctl -u claim-watcher -f` | Live-Logs anschauen |
| `bash /opt/claim/tools/deploy.sh` | Manuelles Deployment |
| `docker-compose -f /opt/claim/docker-compose.prod.yml logs api` | API-Logs |
| `docker-compose -f /opt/claim/docker-compose.prod.yml restart api` | API neustarten |

---

## 📋 Voraussetzungen

- ✅ Ubuntu/Debian Server (22.04 LTS empfohlen)
- ✅ Root oder sudo-Zugriff
- ✅ Internet-Zugang zu GitHub
- ✅ Mindestens 2GB RAM, 10GB Speicher

---

## ❓ Häufige Probleme

**Service startet nicht?**
```bash
sudo journalctl -u claim-watcher -n 50
bash /opt/claim/tools/deploy-watcher.sh  # Manueller Test
```

**Docker funktioniert nicht?**
```bash
sudo systemctl start docker
docker ps  # Test-Befehl
```

**Datenbank-Fehler?**
```bash
docker-compose -f /opt/claim/docker-compose.prod.yml exec db pg_isready
```

---

## 📚 Vollständige Dokumentation

Siehe [DEPLOYMENT.md](DEPLOYMENT.md) für erweiterte Konfiguration, Sicherheit, Monitoring und Skalierung.

---

**Version:** 1.0.0
