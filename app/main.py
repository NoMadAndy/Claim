from fastapi import FastAPI, Request, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import os

from app.database import get_db
from app.routers import auth, spots, logs, claims, tracks, items
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
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Claim GPS Game</h1><p>Frontend not found</p>")

# Serve static files (CSS, JS)
@app.get("/styles.css")
async def serve_css():
    """Serve CSS file"""
    css_path = os.path.join(frontend_path, "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    return Response(content="/* CSS not found */", media_type="text/css", status_code=404)

@app.get("/favicon.svg")
async def serve_favicon():
    """Serve favicon"""
    favicon_path = os.path.join(frontend_path, "favicon.svg")
    if os.path.exists(favicon_path):
        with open(favicon_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="image/svg+xml")
    return Response(content="", media_type="image/svg+xml", status_code=404)

@app.get("/app.js")
async def serve_js():
    """Serve JavaScript file"""
    js_path = os.path.join(frontend_path, "app.js")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    return Response(content="// JS not found", media_type="application/javascript", status_code=404)


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
