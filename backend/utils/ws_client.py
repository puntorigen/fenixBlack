import asyncio
import json
import websockets

class WebSocketClient:
    def __init__(self, meeting_id, uri_base="ws://localhost:8000"):
        self.meeting_id = meeting_id
        self.uri = f"{uri_base}/meeting/{meeting_id}"
        self.websocket = None

    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"Connected to {self.uri}")
            return True
        except Exception as e:
            print(f"Failed to connect to {self.uri}: {e}")
            return False

    async def disconnect(self):
        """Disconnect the WebSocket connection."""
        if self.websocket:
            await self.websocket.close()
            print("Disconnected from the WebSocket server.")

    async def send(self, data):
        """Send a command to the WebSocket server."""
        message = json.dumps(data)
        if self.websocket:
            await self.websocket.send(message)
            print(f"Sent: {message}")

    async def listen_for_messages(self, on_message):
        """Receive messages from the WebSocket server and process them."""
        try:
            while self.websocket:
                response = await self.websocket.recv()
                message = json.loads(response)
                print(f"Received: {message}")
                # Implement custom handling based on message content
                if await on_message(message):
                    break
        except websockets.exceptions.ConnectionClosed:
            print("Connection with server closed.")

    async def handle_message(self, message):
        """Handle incoming messages based on their type or content."""
        if 'action' in message and message['action'] == 'session_key':
            print(f"Session key received: {message['key']}")
        if 'action' in message and message['action'] == 'end':
            print("End message received. Closing connection.")
            await self.disconnect()
            return True  # Return True to indicate the connection should close
        return False

    async def run(self):
        """Manage the connection and listen for messages."""
        if await self.connect():
            await self.listen_for_messages()

# Example usage
#if __name__ == "__main__":
#    client = WebSocketClient("12345")  # Example meeting ID
#    asyncio.run(client.run())
