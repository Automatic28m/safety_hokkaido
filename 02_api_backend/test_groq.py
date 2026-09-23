import requests
from config import config

payload = {
    "model": config.LLM_MODEL,
    "messages": [{"role": "user", "content": "What is the weather?"}],
    "temperature": 0.2,
    "max_tokens": 100
}

headers = {
    "Authorization": f"Bearer {config.GROQ_API_KEY}",
    "Content-Type": "application/json"
}

res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
print(res.status_code, res.text)
