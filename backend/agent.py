import asyncio
import json
import traceback
from datetime import datetime

from fastmcp.tools import tool
from ibm_llm_client import ask_llm
from fastmcp import Client as MCPClient
from mcp_server import mcp
from prompts import SYSTEM_PROMPT, USER_PROMPT


class Agent:
    """Agent class that maintains conversation history and interacts with the LLM client."""

    def __init__(self, websocket_server):
        self.websocket_server = websocket_server
        self.is_running = False
        self.system_prompt = SYSTEM_PROMPT
        self.user_prompt = USER_PROMPT
        self.conversation = [self.system_prompt, self.user_prompt]
        self.MCPclient = None
        self.tools = None



    async def start_agent(self):
        """Starts the agent's main loop."""
        async with MCPClient(mcp) as client:
            self.MCPclient = client
            await self._get_tools()
            await self._agent_loop(interval=60)  # Run agent loop every 60 seconds

    def stop_agent(self):
        """Stops the agent's main loop."""
        self.is_running = False

    async def _agent_loop(self, interval: int = 60):
        self.is_running = True
        print("Agent loop started.")
        while self.is_running:
            try:
                await self._get_recommendation()
            except Exception as e:
                print(f"Error occurred in agent loop: {e}\n{traceback.format_exc()}")
            
            self.conversation = [self.system_prompt, self.user_prompt]   # Reset conversation history for the next iteration
            await asyncio.sleep(interval)  # Sleep briefly to ensure any ongoing processes are completed before fully stopping the agent

    async def _get_recommendation(self):
        """Main loop for getting recommendations from the LLM based on the conversation history."""

        recommendation = None
        max_iterations = 10 # Set a max number of iterations to prevent infinite loops in case of unexpected LLM behavior   
        for iteration in range(max_iterations):
            # prompt the LLM for a recommendation based on the conversation history
            response = await ask_llm(self.conversation, self.tools)

            # parse the response, if its a tool call, execute the tool and add the tool response back to the conversation, if its text, send the recommendation and break the loop
            if response is not None:
                
                # add the raw LLM response to the conversation history for context
                self.conversation.append(response.get("raw_message", {})) 

                response_type = response.get("type") # Check if the response is a tool call or a text recommendation

                # If it's a tool call, execute the tool and add the response to the conversation history
                if response_type == "tool_call":
                    print("Received tool call from LLM.")
                    tool_name = response.get("tool")
                    tool_args = response.get("args")
                    tool_call_id=response.get("tool_call_id")
                    tool_response = await self._execute_tool_call(tool_name, tool_args, tool_call_id)
                    self.conversation.append(tool_response)

                # If it's a text recommendation, send the recommendation and break the loop
                elif response_type == "text": 
                    print("Received recommendation from LLM.")
                    recommendation = response.get("content")
                    await self._send_recommendation(recommendation)
                    return
        
        return None





    async def _get_tools(self):
        """Gets the list of available tools from the MCP server."""
        mcp_tools = await self.MCPclient.list_tools()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in mcp_tools
        ]
        print("Retrieved tools from MCP server.")


    async def _execute_tool_call(self, tool_name, tool_args, tool_call_id):
        """Executes a tool on the MCP server and returns its contents."""
        print(f"TOOL EXECUTION: {tool_name} with args: {tool_args}\n")

        result = await self.MCPclient.call_tool(tool_name, tool_args or {})

        try:
            content = result.content[0].text if result.content else ""

        except Exception as e:
            print(f"Error occurred while parsing tool result: {e}\n{traceback.format_exc()}")
            content = ""


        # print(f"Tool result: {content}")

        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }




    async def _send_recommendation(self, recommendation):
        """Broadcasts the LLM recommendation to all connected frontend clients."""
        message = json.dumps({
            "type": "recommendation",
            "flight_id": "DL447",
            "content": recommendation,
            "timestamp": datetime.now().isoformat(),
        })

        # Send the recommendation to all connected clients
        await self.websocket_server.broadcast(message)
        print("Message broadcasted.")
        # print(self.conversation)



