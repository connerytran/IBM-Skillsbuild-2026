

from ibm_watsonx_ai import Credentials, APIClient
from dotenv import load_dotenv
from ibm_watsonx_ai.foundation_models import ModelInference
import config
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


def testModel():
    messages = [
        {"role": "user", "content": "Glaze Lebron like crazy"}
    ]
    response = model.chat(messages=messages)
    print(response["choices"][0]["message"]["content"])



if __name__ == '__main__':
    testModel()



