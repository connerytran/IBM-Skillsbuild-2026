

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
            }
        ]

    def start_agent(self):
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
