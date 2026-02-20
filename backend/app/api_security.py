import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
api_key_header = APIKeyHeader(name="x-api-key")
API_KEY = os.getenv("API_KEY")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")