from fastapi import FastAPI, Request, Depends, WebSocket
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os
from datetime import datetime

from app.database import get_db
from app.routers import auth, spots, logs, claims, tracks, items, loot
from app.ws.handlers import websocket_endpoint
from app.config import settings


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


# Lightweight client log sink for debugging (stdout only, no auth)
@app.post("/api/client-log")
async def client_log(payload: dict = Body(...)):
    msg = payload.get("msg", "")
    level = payload.get("level", "INFO")
    if msg:
        # Print to stdout (what you see in server terminal)
        print(f"CLIENTLOG [{level}] {msg}")
        
        # Also write to file for easy access
        try:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "client-debug.log")
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] [{level}] {msg}\n")
                f.flush()
        except Exception as e:
            print(f"ERROR writing log file: {e}")
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
        
        print(f"[{timestamp}] Received connection diagnostics from client")
        
    except Exception as e:
        print(f"ERROR writing diagnostics: {e}")
    
    return {"ok": True}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time communication"""
    await websocket_endpoint(websocket, token)


# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")

# Root endpoint to serve index.html
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the main frontend page"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            # Return with no-cache header to always get latest HTML
            response = HTMLResponse(content=f.read())
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
    return HTMLResponse(content="<h1>Claim GPS Game</h1><p>Frontend not found</p>")

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


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Claim GPS Game",
        "version": "1.0.0"
    }


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
