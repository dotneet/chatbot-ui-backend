import openai
from typing import List, Dict

async def chat(prompt: str, messages: List[Dict] = [], model: Dict = None, key: str = None):
    # copy messages
    messages = messages.copy()
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=4000,
        temperature=0.3,
        stream=True
    )
    for chunk in resp:
        if chunk:
            content = chunk['choices'][0]['delta'].get('content')
            if content:
                print(content)
                yield content