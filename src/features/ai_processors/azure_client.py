
import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

load_dotenv()

azure_chat_openai = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_MODEL"),
    api_version="2024-05-01-preview",
    temperature=0,
    max_tokens=None,
    timeout=120,
    max_retries=2
)