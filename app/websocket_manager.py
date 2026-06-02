# app/websocket_manager.py

from typing import Dict
from fastapi import WebSocket
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
    
    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_notification(self, user_id: int, message: str, notif_type: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json({
                    "type": notif_type,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"Notification sent to user {user_id}: {message}")
            except Exception as e:
                print(f"Error sending to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_all(self, message: str):
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except:
                self.disconnect(user_id)

manager = ConnectionManager()