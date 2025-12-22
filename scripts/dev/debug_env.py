import os
from pathlib import Path

from dotenv import load_dotenv

print(f"Current working directory: {os.getcwd()}")
env_path = Path(".env")
print(f".env exists: {env_path.exists()}")

print("Loading .env...")
load_dotenv()

openai_key = os.getenv("MANUS_OPENAI_API_KEY")
llm_key = os.getenv("MANUS_LLM_API_KEY")


def mask(key):
    if not key:
        return "None"
    if len(key) < 10:
        return key
    return f"{key[:5]}...{key[-5:]}"


print(f"MANUS_OPENAI_API_KEY: {mask(openai_key)}")
print(f"MANUS_LLM_API_KEY: {mask(llm_key)}")

# Simulate config.py logic
import tomllib

try:
    with open("config/config.toml", "rb") as f:
        raw_config = tomllib.load(f)
    print("Loaded config.toml")
    base_llm = raw_config.get("llm", {})
    api_type = base_llm.get("api_type")
    config_key = base_llm.get("api_key")
    print(f"Config API Type: {api_type}")
    print(f"Config API Key: {mask(config_key)}")

    api_key_env = os.getenv("MANUS_LLM_API_KEY")
    if not api_key_env and api_type == "openai":
        print("Fallback to MANUS_OPENAI_API_KEY")
        api_key_env = os.getenv("MANUS_OPENAI_API_KEY")

    final_key = api_key_env or config_key
    print(f"Calculated Final Key: {mask(final_key)}")

except Exception as e:
    print(f"Error loading config.toml: {e}")
