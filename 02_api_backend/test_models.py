import os, requests
from dotenv import load_dotenv
load_dotenv()
url = "https://api.groq.com/openai/v1/models"
headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"}
response = requests.get(url, headers=headers)
print([m["id"] for m in response.json().get("data", [])])
