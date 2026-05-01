
import asyncio
import json
import logging
import websockets
from typing import Set

logging.getLogger("websockets").setLevel(logging.CRITICAL)


class WebSocketServer:
     
     
    def __init__(self, host: str="0.0.0.0", port: int=8765):
        self.host = host
        self.port = port
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set() # Set to keep track of connected clients for WebSocket communication


    async def _handler(self, websocket):
        self.connected_clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")
        try:
            async for message in websocket:         # is an async loop that waits for incoming messages from client. Once message arrives THEN the body is executed then wait again for next new message
                print(f"Received message from client: {message}")
                # Here you can handle incoming messages from the client if needed
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected: {websocket.remote_address}")



    async def start_server(self):
            """Starts Websocket server to communicate with the front-end client."""

            # websockets.serve creates a server on localhost:8765 and uses the handler function to handle incoming connections
            # Everytime a client connects, the handler function will be called. The websockets library automatically passes websocket and path params
            async with websockets.serve(self._handler, self.host, self.port):
                print("WebSocket server started.")
                await asyncio.Future()  # Run forever


    async def broadcast(self, message: str):
        """Sends a message to all connected clients."""
        if self.connected_clients:
            await asyncio.gather(
                *[client.send(message) for client in self.connected_clients], # for every client in the set of connected clients, create a list of coroutines that send the message to each client, and then run them concurrently with asyncio.gather
                return_exceptions=True  # This will allow the broadcast to continue even if one send fails
            )
        else:
            print("No clients connected to receive the message.")
            print(f"Message to broadcast: {message}")
