

import asyncio
from datetime import datetime
from ibm_llm_client import ask_llm


class Agent:
    """Agent class that maintains conversation history and interacts with the LLM client."""

    def __init__(self, tools):
        self.tools = tools
        self.conversation = [
            {
                "role": "system",
                "content": "You are a gate agent assistant monitoring flight DL447. Use the available tools to give a recommendation on whether to close the gate."
            },
            {
                "role": "user",  
                "content": "Please check the current status of flight DL447 and provide a recommendation on whether to close the gate."
            }
        ]

    def start_agent(self):
        """Starts the agent's main loop."""
        self._recommendation_loop()        
        return
    
    def stop_agent(self):
        """Stops the agent's main loop."""
        return
    

    def _recommendation_loop(self):
        """Main loop for getting recommendations from the LLM based on the conversation history."""

        recommendation = None

        while True:
            # prompt the LLM for a recommendation based on the conversation history
            response = ask_llm(self.conversation, self.tools)

            # parse the response, if its a tool call, execute the tool and add the tool response back to the conversation, if its text, send the recommendation and break the loop
            if response is not None:
                
                # add the raw LLM response to the conversation history for context
                self.conversation.append(response.get("raw_message", {})) 

                response_type = response.get("type") # Check if the response is a tool call or a text recommendation

                # If it's a tool call, execute the tool and add the response to the conversation history
                if response_type == "tool_call":
                    tool_name = response.get("tool")
                    tool_args = response.get("args")
                    tool_call_id=response.get("tool_call_id")
                    tool_response = self._execute_tool_call(tool_name, tool_args, tool_call_id)
                    self.conversation.append(tool_response)

                # If it's a text recommendation, send the recommendation and break the loop
                elif response_type == "text": 
                    recommendation = response.get("content")
                    self._send_recommendation(recommendation)
                    break



    def _execute_tool_call(self, tool_name, tool_args, tool_call_id):
        """Executes a tool on the MCP server and returns its contents."""
        # For the sake of this example, we'll mock the tool response. In a real implementation, this would involve making an API call to the MCP server with the tool name and args,
        # and then adding the response back to the conversation history.
        tool_response = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": "15 more minutes until flight departs."
        }

        return tool_response

    def _send_recommendation(self, recommendation):
        print(f"Agent recommendation: {recommendation}")
        return


def main():

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

    agent = Agent(tools)
    agent.start_agent()


if __name__ == '__main__':
    main()
