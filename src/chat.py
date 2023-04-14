from typing import Dict, List, Any, Optional, Iterable
import openai
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")


def adjust_message_size(model: str, messages: List[Dict[Any, Any]], max_token_size: int, output_token_size: int) -> List[Dict[str, str]]:
    encoding = tiktoken.encoding_for_model(model)
    result: List[Dict[str, str]] = []

    total_token_size: int = 0
    # reverse messages
    messages = messages[::-1]
    for message in messages:
        token_size: int = len(encoding.encode(message['content']))
        if total_token_size + token_size + output_token_size > max_token_size:
            break
        total_token_size += token_size
        result.insert(0, message)

    return result


def call_chat_completion(prompt: str, messages: List[Dict[Any, Any]], model: Dict[Any, Any], key: Optional[str] = None) -> Iterable[Dict[Any, Any]]:
    model_name = model['id']
    output_max_tokens = 2000
    messages = adjust_message_size(
        model_name, messages, 4000, output_max_tokens)
    if len(messages) == 0:
        raise ValueError("Your messages are too long.")
    a: Any = openai.ChatCompletion.create(
        model=model_name,
        messages=messages,
        max_tokens=output_max_tokens,
        temperature=0.3,
        stream=True
    )
    return dict(a)


async def generate_chat(resp: Iterable[Dict[Any, Any]]):
    for chunk in resp:
        if chunk:
            content = str(chunk['choices'][0]['delta'].get('content'))
            if content:
                yield content
