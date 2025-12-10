from typing import Dict, Set
from fastapi import WebSocket
from datetime import datetime
import json


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user's websocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's websocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in list(self.active_connections[user_id]):
                try:
                    # Check if connection is still open before sending
                    if connection.client_state.name != 'DISCONNECTED' and connection.application_state.name != 'DISCONNECTED':
                        await connection.send_json(message)
                except RuntimeError as e:
                    # Connection already closed - mark for removal
                    if "close" in str(e).lower() or "disconnected" in str(e).lower():
                        disconnected.append(connection)
                    else:
                        print(f"Runtime error sending to user {user_id}: {e}")
                except Exception as e:
                    print(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast(self, message: dict, exclude_user: int = None):
        """Broadcast message to all connected users"""
        for user_id, connections in list(self.active_connections.items()):
            if exclude_user and user_id == exclude_user:
                continue
            disconnected = []
            for connection in list(connections):
                try:
                    # Check if connection is still open before sending
                    if connection.client_state.name != 'DISCONNECTED' and connection.application_state.name != 'DISCONNECTED':
                        await connection.send_json(message)
                except RuntimeError as e:
                    # Connection already closed
                    if "close" in str(e).lower() or "disconnected" in str(e).lower():
                        disconnected.append(connection)
                    else:
                        print(f"Runtime error broadcasting to user {user_id}: {e}")
                except Exception as e:
                    # Silently ignore connection errors - this is normal
                    disconnected.append(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                connections.discard(conn)
    
    async def broadcast_position(
        self,
        user_id: int,
        username: str,
        latitude: float,
        longitude: float,
        heading: float = None
    ):
        """Broadcast user position update"""
        message = {
            "event_type": "position_update",
            "data": {
                "user_id": user_id,
                "username": username,
                "latitude": latitude,
                "longitude": longitude,
                "heading": heading,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message, exclude_user=user_id)
    
    async def broadcast_log_event(
        self,
        log_id: int,
        user_id: int,
        username: str,
        spot_name: str,
        xp_gained: int,
        claim_points: int,
        is_auto: bool
    ):
        """Broadcast log event"""
        message = {
            "event_type": "log_event",
            "data": {
                "log_id": log_id,
                "user_id": user_id,
                "username": username,
                "spot_name": spot_name,
                "xp_gained": xp_gained,
                "claim_points": claim_points,
                "is_auto": is_auto
            }
        }
        await self.broadcast(message)
    
    async def send_loot_spawn(
        self,
        user_id: int,
        spot_id: int,
        latitude: float,
        longitude: float,
        xp: int,
        item_name: str = None,
        expires_at: str = None
    ):
        """Send loot spawn notification to specific user"""
        message = {
            "event_type": "loot_spawn",
            "data": {
                "spot_id": spot_id,
                "latitude": latitude,
                "longitude": longitude,
                "xp": xp,
                "item_name": item_name,
                "expires_at": expires_at
            }
        }
        await self.send_personal_message(message, user_id)
    
    async def broadcast_claim_update(
        self,
        spot_id: int,
        user_id: int,
        username: str,
        claim_value: float,
        dominance: float
    ):
        """Broadcast claim/dominance update"""
        message = {
            "event_type": "claim_update",
            "data": {
                "spot_id": spot_id,
                "user_id": user_id,
                "username": username,
                "claim_value": claim_value,
                "dominance": dominance
            }
        }
        await self.broadcast(message)
    
    async def broadcast_tracking_update(
        self,
        user_id: int,
        username: str,
        track_id: int,
        is_active: bool,
        distance_km: float = None
    ):
        """Broadcast tracking status update"""
        message = {
            "event_type": "tracking_update",
            "data": {
                "user_id": user_id,
                "username": username,
                "track_id": track_id,
                "is_active": is_active,
                "distance_km": distance_km
            }
        }
        await self.broadcast(message)


# Global connection manager instance
manager = ConnectionManager()
