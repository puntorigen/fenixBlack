from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.rooms = {}
        self.keepalive_tasks = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        if room_id not in self.rooms:
            self.rooms[room_id] = []
            self.keepalive_tasks[room_id] = asyncio.create_task(self.send_keepalive(room_id))
        await websocket.accept()
        self.rooms[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.rooms[room_id].remove(websocket)
        if not self.rooms[room_id]:
            del self.rooms[room_id]
            if room_id in self.keepalive_tasks:
                self.keepalive_tasks[room_id].cancel()
                del self.keepalive_tasks[room_id]

    async def send_message(self, message: str, room_id: str):
        connections = self.rooms.get(room_id, [])
        for connection in list(connections):  # Copy the list to avoid modification during iteration
            try:
                print("ConnectionManager->send_message->send_text",message)
                await connection.send_text(message)
            except Exception as e:
                # Handle disconnections or errors
                connections.remove(connection)
                print(f"Error sending message: {e}")

    async def send_keepalive(self, room_id: str):
        """Send keepalive messages to all clients in the room at regular intervals."""
        try:
            while True:
                await asyncio.sleep(10)  # send a keepalive every 10 seconds
                connections = self.rooms.get(room_id, [])
                for connection in list(connections):  # Copy the list to safely handle disconnections
                    try:
                        await connection.send_text("KEEPALIVE")
                    except Exception as e:
                        # Handle disconnections or errors
                        connections.remove(connection)
                        print(f"Error sending keepalive: {e}")
                if not connections:
                    break  # Stop the keepalive if no connections left
        except asyncio.CancelledError:
            print(f"Keepalive task cancelled for room {room_id}")

