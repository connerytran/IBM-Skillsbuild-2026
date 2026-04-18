
from agent import Agent 
import asyncio
from websocket_server import WebSocketServer

async def main():
    
    websocket_server = WebSocketServer()
    agent = Agent(websocket_server)

    await asyncio.gather( 
        agent.start_agent(),
        websocket_server.start_server()
    )

if __name__ == '__main__':

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
