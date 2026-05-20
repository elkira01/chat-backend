from dotenv import dotenv_values

config = dotenv_values(".env")

WEB_SEARCH_PROVIDER = config.get("WEB_SEARCH_PROVIDER")
WEB_SEARCH_API_KEY = config.get("WEB_SEARCH_API_KEY")
OLLAMA_BASE_URL = config.get("OLLAMA_BASE_URL", "http://localhost:11434")
MAX_SEARCH_RESULTS = config.get("MAX_SEARCH_RESULTS", 3)
MAX_HISTORY_TURNS = config.get("MAX_HISTORY_TURNS", 5)
ALLOWED_ORIGINS = config.get("ALLOWED_ORIGINS", "*")
