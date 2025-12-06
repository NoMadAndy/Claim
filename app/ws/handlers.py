from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database import SessionLocal
from app.config import settings
from app.services import auth_service
from app.ws.connection_manager import manager
import json


async def websocket_endpoint(websocket: WebSocket, token: str):
    """Main WebSocket endpoint"""
    # Create DB session
    db = SessionLocal()
    
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
            
            # Listen for messages
            while True:
                data = await websocket.receive_text()
                
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
                            "data": {}
                        })
                    
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
        
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id)
            print(f"User {user.username} disconnected")
        
        except Exception as e:
            print(f"WebSocket error for user {user.username}: {e}")
            manager.disconnect(websocket, user.id)
    
    finally:
        # Close DB session
        db.close()

