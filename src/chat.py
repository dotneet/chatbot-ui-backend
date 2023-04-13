from typing import Dict, List

import openai
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def adjust_message_size(model: str, messages: List[Dict], max_token_size, output_token_size) -> List[Dict]:
    encoding = tiktoken.encoding_for_model(model)
    result = []

    total_token_size = 0
    # reverse messages
    messages = messages[::-1]
    for message in messages:
        token_size = len(encoding.encode(message['content']))
        if total_token_size + token_size + output_token_size > max_token_size:
            break
        total_token_size += token_size
        result.insert(0, message)

    return result


def call_chat_completion(prompt: str, messages: List[Dict], model: Dict, key: str = None) -> str:
    model_name = model['id']
    output_max_tokens = 2000
    messages = adjust_message_size(
        model_name, messages, 4000, output_max_tokens)
    if len(messages) == 0:
        raise ValueError("Your messages are too long.")
    return openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        max_tokens=output_max_tokens,
        temperature=0.3,
        stream=True
    )


async def generate_chat(resp):
    for chunk in resp:
        if chunk:
            content = chunk['choices'][0]['delta'].get('content')
            if content:
                yield content
