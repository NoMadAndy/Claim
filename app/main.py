from fastapi import FastAPI, Request, Depends, WebSocket
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response, JSONResponse, FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
import re
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import shutil

from app.database import get_db
from app.routers import auth, spots, logs, claims, tracks, items, loot, admin, changelog, server_logs
from app.ws.handlers import websocket_endpoint
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track server start time and connection count for diagnostics
server_start_time = datetime.now()
active_connections = 0

BERLIN = ZoneInfo("Europe/Berlin")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("Starting Claim GPS Game...")
    print(f"Database: {settings.DATABASE_URL}")
    
    # Initialize database
    from app.models import init_db
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Database initialization error: {e}")
    
    yield
    
    # Shutdown
    print("Shutting down Claim GPS Game...")


app = FastAPI(
    title="Claim GPS Game",
    description="Location-based GPS game with claims, tracking, and real-time updates",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for reverse proxy compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for reverse proxy support
@app.middleware("http")
async def reverse_proxy_middleware(request: Request, call_next):
    """Handle reverse proxy headers"""
    if settings.BEHIND_PROXY:
        # Handle X-Forwarded headers
        forwarded_proto = request.headers.get("X-Forwarded-Proto")
        forwarded_host = request.headers.get("X-Forwarded-Host")
        
        if forwarded_proto:
            request.scope["scheme"] = forwarded_proto
        if forwarded_host:
            request.scope["server"] = (forwarded_host, None)
    
    response = await call_next(request)
    return response


# Include routers
app.include_router(auth.router)
app.include_router(spots.router)
app.include_router(logs.router)
app.include_router(claims.router)
app.include_router(tracks.router)
app.include_router(items.router)
app.include_router(loot.router)
app.include_router(admin.router)
app.include_router(changelog.router)
app.include_router(server_logs.router)


# Lightweight client log sink for debugging (stdout only, no auth)
@app.post("/api/client-log")
async def client_log(payload: dict = Body(...)):
    msg = payload.get("msg", "")
    level = payload.get("level", "INFO")
    if msg:
        # Print to stdout (what you see in server terminal)
        print(f"CLIENTLOG [{level}] {msg}")
        
        # Also write to file for easy access (with better error handling)
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "client-debug.log")
            
            # Check if file exists and is getting too large (>10MB), rotate it
            if os.path.exists(log_file):
                if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
                    # Rotate the file
                    import shutil
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_file = f"{log_file}.{timestamp}"
                    shutil.move(log_file, backup_file)
                    logger.info(f"Rotated log file to {backup_file}")
            
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] [{level}] {msg}\n")
                f.flush()
        except PermissionError as e:
            logger.error(f"Permission denied writing log file: {e}")
            # Don't crash on permission errors - just log to stdout
        except Exception as e:
            logger.error(f"ERROR writing log file: {e}")
            # Continue even if logging fails
    return {"ok": True}


# Connection diagnostics endpoint
@app.post("/api/connection-diagnostics")
async def connection_diagnostics(payload: dict = Body(...)):
    """Receive connection diagnostics from client"""
    timestamp = datetime.now().isoformat()
    
    try:
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "connection-diagnostics.log")
        
        # Check if file is getting too large (>50MB), rotate it
        if os.path.exists(log_file):
            if os.path.getsize(log_file) > 50 * 1024 * 1024:  # 50MB
                # Rotate the file
                dt = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{log_file}.{dt}"
                shutil.move(log_file, backup_file)
                logger.info(f"Rotated diagnostics log to {backup_file}")
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] Connection Diagnostics Report\n")
            f.write(f"{'='*80}\n")
            
            # Client info
            if "clientInfo" in payload:
                f.write(f"User: {payload['clientInfo'].get('user', 'N/A')}\n")
                f.write(f"URL: {payload['clientInfo'].get('url', 'N/A')}\n")
            
            # Status
            if "status" in payload:
                f.write(f"\nConnection Status:\n")
                for key, value in payload["status"].items():
                    f.write(f"  {key}: {value}\n")
            
            # Recent errors
            if "recent" in payload:
                f.write(f"\nRecent Errors:\n")
                if payload["recent"].get("apiErrors"):
                    f.write(f"  API Errors ({len(payload['recent']['apiErrors'])}):\n")
                    for err in payload["recent"]["apiErrors"][-3:]:
                        f.write(f"    - {err}\n")
                if payload["recent"].get("wsErrors"):
                    f.write(f"  WebSocket Errors ({len(payload['recent']['wsErrors'])}):\n")
                    for err in payload["recent"]["wsErrors"][-3:]:
                        f.write(f"    - {err}\n")
            
            f.flush()
        
        logger.info(f"Received connection diagnostics from {payload.get('clientInfo', {}).get('user', 'unknown')}")
        
    except PermissionError as e:
        logger.error(f"Permission denied writing diagnostics: {e}")
    except Exception as e:
        logger.error(f"ERROR writing diagnostics: {e}")
    
    return {"ok": True}


# Health check / Keep-Alive endpoint
@app.get("/api/health")
async def health_check():
    """Server health check endpoint - lightweight response for keep-alive"""
    uptime_seconds = (datetime.now() - server_start_time).total_seconds()
    return JSONResponse({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime_seconds,
        "active_connections": active_connections
    })


# Heartbeat endpoint for frequent pings
@app.post("/api/heartbeat")
async def heartbeat(payload: dict = Body(...)):
    """Client heartbeat to keep connection alive"""
    return {"ok": True, "timestamp": datetime.now().isoformat()}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time communication"""
    await websocket_endpoint(websocket, token)


# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")


def _read_git_commit_short(repo_root: str) -> Optional[str]:
    """Read short git commit hash without calling `git`.

    Works in containers where the repository (including .git) is volume-mounted but git isn't installed.
    """
    try:
        git_dir = os.path.join(repo_root, ".git")
        head_path = os.path.join(git_dir, "HEAD")
        if not os.path.exists(head_path):
            return None

        head = open(head_path, "r", encoding="utf-8").read().strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1].strip()
            ref_path = os.path.join(git_dir, ref.replace("/", os.sep))
            if os.path.exists(ref_path):
                sha = open(ref_path, "r", encoding="utf-8").read().strip()
                return sha[:8]

            packed = os.path.join(git_dir, "packed-refs")
            if os.path.exists(packed):
                with open(packed, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith("^"):
                            continue
                        parts = line.split(" ")
                        if len(parts) == 2 and parts[1] == ref:
                            return parts[0][:8]
            return None

        # Detached head
        if re.fullmatch(r"[a-fA-F0-9]{40}", head):
            return head[:8]
        return None
    except Exception:
        return None


def _inject_version_into_html(html: str, *, commit: str, timestamp: str, cache_bust: str) -> str:
    """Inject commit/timestamp and cache-bust query into the HTML (in-memory)."""
    def _toggle_repl(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r"\sdata-commit=\"[^\"]*\"", "", tag)
        tag = re.sub(r"\sdata-timestamp=\"[^\"]*\"", "", tag)
        return tag.replace(
            'id="toggle-debug"',
            f'id="toggle-debug" data-commit="{commit}" data-timestamp="{timestamp}"',
        )

    html = re.sub(
        r"<button\b[^>]*\bid=\"toggle-debug\"[^>]*>",
        _toggle_repl,
        html,
        count=1,
        flags=re.IGNORECASE,
    )

    # Ensure cache busting for CSS/JS
    html = re.sub(r"styles\.css(\?v=[^\"'>\s]+)?", f"styles.css?v={cache_bust}", html)
    html = re.sub(r"app\.js(\?v=[^\"'>\s]+)?", f"app.js?v={cache_bust}", html)
    return html


_DEPLOYED_AT = datetime.now(BERLIN)
_DEPLOYED_AT_STR = _DEPLOYED_AT.strftime('%d.%m.%Y %H:%M:%S')
_CACHE_BUST = str(int(_DEPLOYED_AT.timestamp()))


# Root endpoint to serve index.html
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page"""
    index_path = os.path.join(frontend_path, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse(content="<h1>Claim GPS Game</h1><p>Frontend not found</p>")

    with open(index_path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Prefer explicit env override (useful for some deploy setups)
    commit = (os.environ.get("CLAIM_COMMIT") or "").strip()
    if not commit:
        repo_root = os.path.abspath(os.path.join(frontend_path, ".."))
        commit = _read_git_commit_short(repo_root) or "deployed"

    html = _inject_version_into_html(
        raw,
        commit=commit,
        timestamp=os.environ.get("CLAIM_DEPLOYED_AT") or _DEPLOYED_AT_STR,
        cache_bust=os.environ.get("CLAIM_CACHE_BUST") or _CACHE_BUST,
    )

    response = HTMLResponse(content=html)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Serve static files (CSS, JS)
@app.get("/styles.css")
async def serve_css():
    """Serve CSS file"""
    css_path = os.path.join(frontend_path, "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            # CSS can be cached longer since we use cache busters
            response = Response(content=f.read(), media_type="text/css")
            response.headers["Cache-Control"] = "public, max-age=3600"
            return response
    return Response(content="/* CSS not found */", media_type="text/css", status_code=404)

@app.get("/app.js")
async def serve_js():
    """Serve JavaScript file"""
    js_path = os.path.join(frontend_path, "app.js")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            # JS can be cached longer since we use cache busters
            response = Response(content=f.read(), media_type="application/javascript")
            response.headers["Cache-Control"] = "public, max-age=3600"
            return response
    return Response(content="/* JS not found */", media_type="application/javascript", status_code=404)

@app.get("/admin.html")
async def serve_admin():
    """Serve admin dashboard"""
    admin_path = os.path.join(frontend_path, "admin.html")
    if os.path.exists(admin_path):
        with open(admin_path, "r", encoding="utf-8") as f:
            response = HTMLResponse(content=f.read())
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    return HTMLResponse(content="<h1>Admin Dashboard Not Found</h1>", status_code=404)

@app.get("/sounds/{filename}")
async def serve_sound(filename: str):
    """Serve sound files from frontend/sounds/"""
    # Security: Only allow specific filenames to prevent directory traversal
    allowed_files = [
        "Yum_CMaj.wav",
        "Sound LD Bumpy Reconstruction_keyC#min.wav",
        "TR 727 Beat 3_125bpm.wav",
        "DN_DSV_Vocal_Yeah_02_KeyBmin_56bpm.wav"
    ]
    
    # URL decode the filename (handle encoded characters like %23 for # and %20 for space)
    import urllib.parse
    decoded_filename = urllib.parse.unquote(filename)
    
    if decoded_filename not in allowed_files:
        return Response(content="Not Found", status_code=404)
    
    sound_path = os.path.join(frontend_path, "sounds", decoded_filename)
    if os.path.exists(sound_path):
        with open(sound_path, "rb") as f:
            response = Response(content=f.read(), media_type="audio/wav")
            response.headers["Cache-Control"] = "public, max-age=86400"
            return response
    return Response(content="Not Found", status_code=404)

@app.get("/favicon.svg")
async def serve_favicon():
    """Serve favicon"""
    favicon_path = os.path.join(frontend_path, "favicon.svg")
    if os.path.exists(favicon_path):
        with open(favicon_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="image/svg+xml")
    return Response(content="", media_type="image/svg+xml", status_code=404)

@app.get("/manifest.json")
async def serve_manifest():
    """Serve PWA manifest"""
    manifest_path = os.path.join(frontend_path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/json")
    return Response(content="{}", media_type="application/json", status_code=404)


# Root API info
@app.get("/api")
async def api_info():
    """API information"""
    return {
        "name": "Claim GPS Game API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "spots": "/api/spots",
            "logs": "/api/logs",
            "claims": "/api/claims",
            "tracks": "/api/tracks",
            "items": "/api/items",
            "stats": "/api/stats",
            "websocket": "/ws"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
