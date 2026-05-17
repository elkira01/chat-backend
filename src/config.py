import os
from python_dotenv import dotenv_values

config = dotenv_values(".env")

WEB_SEARCH_PROVIDER = config["WEB_SEARCH_PROVIDER"]
WEB_SEARCH_API_KEY = config["WEB_SEARCH_API_KEY"]
OLLAMA_BASE_URL = config["OLLAMA_BASE_URL"]
OLLAMA_MODEL = config["OLLAMA_MODEL"]
MAX_SEARCH_RESULTS = config["MAX_SEARCH_RESULTS"]
MAX_HISTORY_TURNS = config["MAX_HISTORY_TURNS"]
ALLOWED_ORIGINS = config["ALLOWED_ORIGINS"]
