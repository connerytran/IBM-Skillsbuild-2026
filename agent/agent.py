

import asyncio
import json
from datetime import datetime
from ibm_llm_client import ask_llm
from typing import List, Dict

class Agent:
    """Agent class that maintains conversation history and interacts with the LLM client."""

    def __init__(self, websocket_server):
        self.tools = None
        self.websocket_server = websocket_server
        self.is_running = False
        self.system_prompt = {
            "role": "system",
            "content": "You are a gate agent assistant monitoring flight DL447. Use the available tools to give a recommendation on whether to close the gate."
        }
        self.user_prompt = {
            "role": "user",  
            "content": "Please check the current status of flight DL447 and provide a short recommendation on whether to close the gate."
        }
        self.conversation = [self.system_prompt, self.user_prompt]




    async def start_agent(self):
        """Starts the agent's main loop."""
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
                print(f"Error occurred in agent loop: {e}")
            
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
                    print("Received tool call from LLM. Executing tool...")
                    tool_name = response.get("tool")
                    tool_args = response.get("args")
                    tool_call_id=response.get("tool_call_id")
                    tool_response = await self._execute_tool_call(tool_name, tool_args, tool_call_id)
                    print("Tool executed.")
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
        self.tools = [
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




    async def _execute_tool_call(self, tool_name, tool_args, tool_call_id):
        """Executes a tool on the MCP server and returns its contents."""
        # For the sake of this example, we'll mock the tool response. In a real implementation, this would involve making an API call to the MCP server with the tool name and args,
        # and then adding the response back to the conversation history.
        tool_response = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": "15 more minutes until flight departs."
        }
        return tool_response





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






