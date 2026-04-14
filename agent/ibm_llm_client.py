

from ibm_watsonx_ai import Credentials, APIClient
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference
import config
import json
import asyncio

load_dotenv()

WATSONX_API_KEY    = config.WATSONX_API_KEY
WATSONX_PROJECT_ID = config.WATSONX_PROJECT_ID
WATSONX_URL        = config.WATSONX_URL
MODEL_ID           = config.MODEL_ID

credentials = Credentials(url=WATSONX_URL,
                          api_key=WATSONX_API_KEY)
client = APIClient(credentials=credentials)
params = {
    'max_new_tokens': 512,
}
model = ModelInference(model_id=MODEL_ID, 
                       api_client=client, 
                       project_id=WATSONX_PROJECT_ID)


async def testModel():
    messages = [
        {"role": "user", "content": "Glaze Lebron like crazy"}
    ]
    response = await model.chat(messages=messages)
    print(response["choices"][0]["message"]["content"])



async def ask_llm(messages, tools):
    """
    Send a conversation to the LLM and return a structured response.

    Args:
        messages: list of message dicts with role and content
        tools:    list of tool schemas from the MCP server

    Returns:
        {"type": "tool_call", "tool": str, "args": dict, "raw_message": dict}
        {"type": "text", "content": str, "raw_message": dict}
    """

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        lambda: model.chat(messages=messages, tools=tools)
    )

    message = response['choices'][0]['message']
    if message.get('tool_calls'):
        tool_name = message['tool_calls'][0]['function']['name']                      # Contains the name of the tool to call
        tool_args = json.loads(message["tool_calls"][0]["function"]["arguments"])     # Contains the params of the tool to call
        tool_call_id = message['tool_calls'][0]['id']                                 # Contains the unique id of the tool call, which should be included in the tool response for context
        return {"type": "tool_call", 
                "tool": tool_name, 
                "args": tool_args,
                "tool_call_id": tool_call_id,
                "raw_message": message}

    else:
        content = message['content']
        return {"type": "text",
                "content": content,
                "raw_message": message}



if __name__ == '__main__':

    test_tools = [
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

    test_messages = [
        {
            "role": "system",
            "content": "You are a gate agent assistant monitoring flight DL447. Use the available tools to assess the flight status."
        },
        {
            "role": "user",
            "content": "How much time is left until departure?"
        }
    ]

    result = asyncio.run(ask_llm(test_messages, test_tools))
    print(result)


