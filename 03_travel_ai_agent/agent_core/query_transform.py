import requests
from config import config

class QueryTransformer:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "qwen/qwen3.8-27b"
        
    def translate_to_english(self, query):
        """Translates a foreign query into English so the database can understand it perfectly."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "You are a professional translator. You MUST translate the user's input into English. DO NOT answer the user's question. ONLY output the English translation."
                },
                {
                    "role": "user", 
                    "content": f"Translate this into English: {query}"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        if self.api_key:
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    english_query = response.json()["choices"][0]["message"]["content"].strip()
                    if english_query:
                        return english_query
            except Exception as e:
                print(f"Translation Error (Groq): {e}")

        # Fallback to Gemini
        gemini_key = getattr(config, "GEMINI_API_KEY", "")
        if gemini_key:
            try:
                gemini_headers = {
                    "Authorization": f"Bearer {gemini_key}",
                    "Content-Type": "application/json",
                }
                gemini_payload = {
                    "model": getattr(config, "GEMINI_MODEL", "gemini-flash-latest"),
                    "messages": payload["messages"],
                    "temperature": 0.1,
                    "max_tokens": 500,
                }
                gemini_res = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    headers=gemini_headers,
                    json=gemini_payload,
                    timeout=10
                )
                if gemini_res.status_code == 200:
                    return gemini_res.json()["choices"][0]["message"]["content"].strip()
            except Exception as ex:
                print(f"Translation Error (Gemini): {ex}")
                
        return query

    def reformulate_query(self, query, chat_history):
        """Rewrites a contextual follow-up query into a Standalone Query using the chat history."""
        if not chat_history:
            return query
            
        history_str = ""
        for msg in chat_history[-4:]:
            role = "AI" if msg["role"] in ["ai", "assistant"] else "User"
            history_str += f"{role}: {msg['content']}\n"
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system", 
                    "content": "Given the following conversation history and the user's follow-up question, rephrase the follow-up question to be a standalone question that can be understood without the history. DO NOT answer the question. ONLY output the standalone question."
                },
                {
                    "role": "user", 
                    "content": f"Chat History:\n{history_str}\n\nFollow-up question: {query}\n\nStandalone question:"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 200
        }
        
        if self.api_key:
            try:
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=10)
                if response.status_code == 200:
                    standalone = response.json()["choices"][0]["message"]["content"].strip()
                    if standalone:
                        return standalone
            except Exception as e:
                print(f"Reformulation Error (Groq): {e}")

        # Fallback to Gemini
        gemini_key = getattr(config, "GEMINI_API_KEY", "")
        if gemini_key:
            try:
                gemini_headers = {
                    "Authorization": f"Bearer {gemini_key}",
                    "Content-Type": "application/json",
                }
                gemini_payload = {
                    "model": getattr(config, "GEMINI_MODEL", "gemini-flash-latest"),
                    "messages": payload["messages"],
                    "temperature": 0.1,
                    "max_tokens": 200,
                }
                gemini_res = requests.post(
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    headers=gemini_headers,
                    json=gemini_payload,
                    timeout=10
                )
                if gemini_res.status_code == 200:
                    return gemini_res.json()["choices"][0]["message"]["content"].strip()
            except Exception as ex:
                print(f"Reformulation Error (Gemini): {ex}")

        return query
