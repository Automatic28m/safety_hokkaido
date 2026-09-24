import os
import requests
import json
import sys

def main():
    diff = os.getenv("PR_DIFF")
    if not diff:
        print("No PR diff provided.")
        return

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("Error: GROQ_API_KEY is not set in GitHub Secrets.")
        sys.exit(1)

    # ---------------------------------------------------------
    # The Prompt containing your strict Architectural Rules
    # ---------------------------------------------------------
    system_prompt = """You are the Lead Architect for the Safety Hokkaido project.
Review the following code diff for a Pull Request targeting the 'develop' branch.

STRICT ARCHITECTURAL RULES TO CHECK:
1. Module 07 (Decision LLM Engine) MUST NOT make any network/API calls (no requests.get, no tool loops). It must be a pure synthesizer relying on provided evidence.
2. Module 03 (Travel AI Agent) is responsible for routing, tool calling, and managing conversation history by `conversation_id`.
3. Backend (Module 02) must not hide errors behind HTTP 200. It should return 400, 500, or 503 for errors.
4. Ensure variables like 'safety_level' and 'notices' are outputted correctly in JSON formats.

YOUR TASK:
Provide a concise, constructive review. 
- If the code violates any of the rules above, highlight it in **bold** and explain why it's a security/architecture risk.
- If the code looks safe and follows the rules, state: '✅ **Approved: No architectural violations detected.**'
"""

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the PR diff:\n\n```diff\n{diff}\n```"}
        ],
        "temperature": 0.1
    }

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    print("Sending diff to Groq API...")
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        review = response.json()["choices"][0]["message"]["content"]
        
        # Write to a file so GitHub Actions can read it and post it as a comment
        with open("review_output.md", "w") as f:
            f.write(review)
        print("Review successfully generated.")
    else:
        print(f"Error calling Groq API: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
