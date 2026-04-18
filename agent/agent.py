import asyncio
import json
import traceback
from typing import List, Dict
from datetime import datetime

from fastmcp.tools import tool
from ibm_llm_client import ask_llm
from fastmcp import Client as MCPClient
from mcp_server import mcp


class Agent:
    """Agent class that maintains conversation history and interacts with the LLM client."""

    def __init__(self, websocket_server):
        self.websocket_server = websocket_server
        self.is_running = False
        self.system_prompt = {
            "role": "system",
            "content": (
                "You are an experienced gate agent assistant for flight DL447. "
                "Your job is to assess ALL available flight data before making a gate decision. "
                "You must call every available tool and carefully review each result. "
                "Never make a recommendation based on partial information — a wrong decision causes delays or safety issues.\n\n"

                "GATE ACTIONS AND WHEN TO USE THEM:\n"
                "- CLOSE GATE: Physically close the jet bridge and stop boarding. Use this when the flight is ready to push back — "
                "all or nearly all passengers boarded, no bag pull risks, captain checked in, ground ops complete, and departure is under 15 minutes away.\n"
                "- HOLD GATE: Keep the gate open and continue waiting. Use this when the flight is not yet ready — "
                "passengers still boarding or clearing TSA, connecting passengers inbound within 20 minutes, "
                "bag pull risks exist, ground ops incomplete, or departure is more than 15 minutes away.\n"
                "- OPEN GATE: Reopen or do not close the gate due to a critical blocking issue — "
                "captain is not checked in (flight legally cannot depart), a significant number of bag pull risks exist, "
                "or a ground ops issue prevents safe departure.\n\n"

                "KEY RULES:\n"
                "- A flight cannot depart without the Captain checked in.\n"
                "- If a passenger's bag is loaded but they have not boarded, removing it causes a 20-40 minute delay.\n"
                "- Connecting passengers close to arrival (under 20 min) are worth waiting for.\n"
                "- Negative minutes to departure means the flight is already past scheduled departure — factor in urgency.\n\n"

                "Respond in this exact format:\n\n"
                "- <reason 1>\n"
                "- <reason 2>\n"
                "- <reason 3>\n\n"
                "[CLOSE GATE | HOLD GATE | OPEN GATE]\n"
                "<one sentence summary of your decision>\n\n"
                "List all your reasons first, then make your decision based on them. "
                "Use 3-5 bullet points. Each bullet on its own line. No extra commentary.\n"
                "Be specific — cite exact numbers, names, and times from the data. "
                "For example: '14/20 passengers boarded', 'Passenger John Smith has a loaded bag but has not boarded', "
                "'Captain not checked in', 'Catering incomplete', '8 minutes until departure', "
                "'Connecting passenger arriving in 13 minutes on flight UA302'."
            )
        }
        self.user_prompt = {
            "role": "user",
            "content": "Check the current status of flight DL447 and give your gate recommendation."
        }
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

        message = json.dumps({
            "type": "recommendation",
            "flight_id": "DL447",
            "content": recommendation,
            "timestamp": datetime.now().isoformat()
        })

        # Send the recommendation to all connected clients
        await self.websocket_server.broadcast(message)
        print("Message broadcasted.")
        print(self.conversation)



