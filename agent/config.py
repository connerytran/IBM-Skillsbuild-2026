from dotenv import load_dotenv
import os

load_dotenv()

WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
MODEL_ID           = "meta-llama/llama-3-3-70b-instruct"

SUPABASE_URL       = os.getenv("SUPABASE_URL")
SUPABASE_KEY       = os.getenv("SUPABASE_KEY")

FLIGHT_ID          = "DL447"
