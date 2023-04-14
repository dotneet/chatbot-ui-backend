from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import agent, chat

load_dotenv()


class ChatRequest(BaseModel):
    prompt: str
    messages: List[Dict[str, str]] = []
    model: Dict[Any, Any]
    key: Optional[str] = None


app = FastAPI()


@app.post("/api/chat")
async def post_chat(request: ChatRequest, response: Response):
    try:
        last_message: List[Dict[str, str]] = request.messages[-1:]
        query = last_message[0]['content']
        if query.startswith('!'):
            messages: List[Dict[str, str]] = []
            for message in request.messages:
                if message['content'].startswith('!'):
                    messages.append(
                        {'role': message['role'], 'content': message['content'][1:]})
                else:
                    messages.append(message)
            resp = chat.call_chat_completion(request.prompt, messages,
                                             request.model, request.key)
            return StreamingResponse(chat.generate_chat(resp))
        else:
            return StreamingResponse(agent.query(query))
    except ValueError as e:
        return Response(str(e), status_code=500)
