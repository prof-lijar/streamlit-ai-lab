import ollama

_client = ollama.Client(host="http://localhost:11434")


def list_models(include_cloud: bool = False) -> list[str]:
    response = _client.list()
    models = [m.model for m in response.models]
    if not include_cloud:
        models = [m for m in models if not m.endswith(":cloud")]
    return models


def chat_stream(model: str, messages: list[dict]):
    stream = _client.chat(model=model, messages=messages, stream=True)
    for chunk in stream:
        token = chunk.message.content
        if token:
            yield token
