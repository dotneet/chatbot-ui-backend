from typing import Dict, List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


class ChatRequest(BaseModel):
    prompt: str
    messages: List[Dict] = [] 
    model: Dict
    key: str = None

app = FastAPI()

@app.post("/api/chat")
def chat(request: ChatRequest):
    print(request)
    return "Hello World"
