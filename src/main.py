from typing import Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import chat

load_dotenv()

class ChatRequest(BaseModel):
    prompt: str
    messages: List[Dict] = [] 
    model: Dict
    key: str = None

app = FastAPI()

@app.post("/api/chat")
async def post_chat(request: ChatRequest, response: Response):
    return StreamingResponse(
        chat.chat(request.prompt, request.messages, request.model, request.key)
        )
