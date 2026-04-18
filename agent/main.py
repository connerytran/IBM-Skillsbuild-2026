
from agent import Agent 
import asyncio
from websocket_server import WebSocketServer

async def main():
    websocket_server = WebSocketServer()
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_time_to_departure",
                "description": "Returns the number of minutes remaining until flight DL447 departs.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]
    agent = Agent(tools, websocket_server)

    await asyncio.gather( 
        agent.start_agent(),
        websocket_server.start_server()
    )

if __name__ == '__main__':

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")
