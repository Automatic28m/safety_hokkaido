import requests
import json
from config import config
from src.tools import (
    get_real_time_weather, WEATHER_TOOL_SCHEMA,
    get_disaster_warnings, DISASTER_TOOL_SCHEMA,
    check_train_status, TRAIN_TOOL_SCHEMA
)

class Generator:
    def __init__(self):
        self.api_key = config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = config.LLM_MODEL

    def generate(self, query, context_chunks, chat_history=None, enabled_agents=None):
        if not config.USE_LLM:
            return "DEBUG MODE (LLM OFF):\n\n" + "\n\n".join([f"[{c['metadata']['situation']}] {c['text']}" for c in context_chunks])
            
        if enabled_agents is None:
            enabled_agents = {"weather": True, "disaster": True, "train": True}
            
        context_str = "\n\n".join([f"Source ({c['metadata']['situation']}): {c['text']}" for c in context_chunks])
        system_prompt = config.SYSTEM_PROMPT.replace("{context}", context_str)
        
        # Dynamically build the tools array based on toggles
        active_tools = []
        if enabled_agents.get("weather"):
            active_tools.append(WEATHER_TOOL_SCHEMA)
        else:
            system_prompt = system_prompt.replace("- use `get_weather_for_city` if asked about current weather or driving conditions.", "")
            
        if enabled_agents.get("disaster"):
            active_tools.append(DISASTER_TOOL_SCHEMA)
        else:
            system_prompt = system_prompt.replace("- use `get_disaster_warnings` if asked about current earthquakes, warnings, or if it is safe to travel today.", "")
            
        if enabled_agents.get("train"):
            active_tools.append(TRAIN_TOOL_SCHEMA)
        else:
            system_prompt = system_prompt.replace("- use `check_train_status` if asked about JR Hokkaido trains, airport access, or transit delays.", "")
            
        if not active_tools:
            system_prompt = system_prompt.replace("6. You have access to real-time tools. You MUST use them when relevant:", "6. You do NOT have access to live real-time tools right now. Answer using ONLY the context provided.")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            recent_history = chat_history[-6:]
            for msg in recent_history:
                role = "assistant" if msg["role"] == "ai" else msg["role"]
                messages.append({"role": role, "content": msg["content"]})
        else:
            messages.append({"role": "user", "content": query})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1000
        }
        
        if active_tools:
            payload["tools"] = active_tools
            payload["tool_choice"] = "auto"
        else:
            # Bug fix: explicitly disable ALL tools (including built-in browser.search)
            # Without this, gpt-oss-120b falls back to its own browser tool even
            # when we pass no tools, causing "Tool choice is none, but model called a tool"
            payload["tool_choice"] = "none"
        
        # Initial request to Groq with Tools and RAG context
        response = requests.post(self.api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"Groq API Error: {response.text}")
            return "Sorry, I am having trouble connecting to my Groq AI brain right now."

        response_data = response.json()
        message = response_data["choices"][0]["message"]
        
        # If Groq decides it needs to call one or more tools
        if "tool_calls" in message and message["tool_calls"]:
            messages.append(message)
            
            for tool_call in message["tool_calls"]:
                func_name = tool_call["function"]["name"]
                args = json.loads(tool_call["function"]["arguments"])
                print(f"Tool Triggered! Executing: {func_name} with {args}")
                
                tool_result = ""
                if func_name == "get_weather_for_city":
                    tool_result = get_real_time_weather(args.get("city", "Sapporo"))
                elif func_name == "get_disaster_warnings":
                    tool_result = get_disaster_warnings(args.get("region", "Hokkaido"))
                elif func_name == "check_train_status":
                    tool_result = check_train_status(args.get("line_name", "All"))
                    
                messages.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": func_name,
                    "content": tool_result
                })
                    
            # Send the final request back to Groq (which now contains RAG Rules + Real-Time Data)
            payload["messages"] = messages
            payload["tool_choice"] = "none"  # Prevent it from calling tools *again* in a loop
            
            final_response = requests.post(self.api_url, headers=headers, json=payload)
            if final_response.status_code == 200:
                return final_response.json()["choices"][0]["message"]["content"]
            else:
                print(f"[Generator] Groq API Final Error: {final_response.text}")
                return "Failed to generate final response after fetching tool data."
                
        else:
            # If no tools were needed, just return the standard RAG answer
            return message.get("content", "")
