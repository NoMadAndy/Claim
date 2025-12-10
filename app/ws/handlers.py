from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database import SessionLocal
from app.config import settings
from app.services import auth_service
from app.ws.connection_manager import manager
import json
import asyncio
from datetime import datetime


async def websocket_endpoint(websocket: WebSocket, token: str):
    """Main WebSocket endpoint"""
    # Create DB session
    db = SessionLocal()
    last_heartbeat = datetime.now()
    heartbeat_interval = 30  # Send heartbeat every 30 seconds
    
    try:
        # Authenticate user
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                await websocket.close(code=1008)
                return
        except JWTError:
            await websocket.close(code=1008)
            return
        
        user = auth_service.get_user_by_username(db, username=username)
        if user is None:
            await websocket.close(code=1008)
            return
        
        # Connect user
        await manager.connect(websocket, user.id)
        print(f"[{datetime.now().isoformat()}] User {user.username} connected to WebSocket")
        
        try:
            # Send welcome message
            await websocket.send_json({
                "event_type": "connected",
                "data": {
                    "user_id": user.id,
                    "username": user.username,
                    "message": "Connected to Claim WebSocket"
                }
            })
            
            # Listen for messages with timeout handling
            while True:
                # Check if we need to send heartbeat
                now = datetime.now()
                if (now - last_heartbeat).total_seconds() >= heartbeat_interval:
                    try:
                        await websocket.send_json({
                            "event_type": "heartbeat",
                            "data": {"timestamp": now.isoformat()}
                        })
                        last_heartbeat = now
                    except Exception as e:
                        print(f"[{datetime.now().isoformat()}] Heartbeat failed for {user.username}: {e}")
                        break
                
                try:
                    # Wait for message with timeout
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=heartbeat_interval + 10)
                    
                    try:
                        message = json.loads(data)
                        event_type = message.get("event_type")
                        event_data = message.get("data", {})
                        
                        # Handle different event types
                        if event_type == "position_update":
                            # Broadcast position to other users
                            await manager.broadcast_position(
                                user.id,
                                user.username,
                                event_data.get("latitude"),
                                event_data.get("longitude"),
                                event_data.get("heading")
                            )
                        
                        elif event_type == "ping":
                            # Respond to ping
                            await websocket.send_json({
                                "event_type": "pong",
                                "data": {"timestamp": datetime.now().isoformat()}
                            })
                        
                        elif event_type == "heartbeat":
                            # Client heartbeat - just acknowledge
                            pass
                        
                        else:
                            # Echo unknown event types
                            await websocket.send_json({
                                "event_type": "error",
                                "data": {"message": f"Unknown event type: {event_type}"}
                            })
                    
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "event_type": "error",
                            "data": {"message": "Invalid JSON"}
                        })
                
                except asyncio.TimeoutError:
                    # Timeout waiting for message - connection might be dead
                    print(f"[{datetime.now().isoformat()}] WebSocket timeout for {user.username}")
                    break
        
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id)
            print(f"[{datetime.now().isoformat()}] User {user.username} disconnected")
        
        except Exception as e:
            # Log the actual error message instead of just "Unknown error"
            error_msg = str(e) if str(e) else type(e).__name__
            print(f"[{datetime.now().isoformat()}] WebSocket error for user {user.username}: {error_msg}")
            logger_ws = __import__('logging').getLogger(__name__)
            logger_ws.error(f"WebSocket error for {user.username}: {error_msg}", exc_info=True)
            try:
                manager.disconnect(websocket, user.id)
            except:
                pass  # Already disconnected
    
    finally:
        # Close DB session
        db.close()
