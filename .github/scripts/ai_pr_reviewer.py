import os
import requests
import json
import sys

def main():
    diff = os.getenv("PR_DIFF")
    if not diff:
        print("No PR diff provided.")
        return
        
    # Truncate diff to max 12000 chars (approx 3000-4000 tokens) to prevent rate limits
    if len(diff) > 12000:
        diff = diff[:12000] + "\n...[DIFF TRUNCATED DUE TO TOKEN LIMITS]..."

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("Error: GROQ_API_KEY is not set in GitHub Secrets.")
        sys.exit(1)

    # ---------------------------------------------------------
    # The Prompt containing your strict Architectural Rules
    # ---------------------------------------------------------
    
    # Read the full architectural guidelines from the rules file
    try:
        with open(".github/rules/architecture_guidelines.md", "r", encoding="utf-8") as f:
            architecture_rules = f.read()
    except FileNotFoundError:
        print("Warning: .github/rules/architecture_guidelines.md not found. Falling back to default rules.")
        architecture_rules = "Follow general best practices for Safety Hokkaido."

    system_prompt = f"""You are the Lead Architect for the Safety Hokkaido project.
Review the following code diff for a Pull Request targeting the 'develop' branch.

You MUST enforce the project's strict implementation rules, JSON boundaries, and architecture contracts.
Here is the official Integration Contract for all 8 modules:

<INTEGRATION_CONTRACT>
{architecture_rules}
</INTEGRATION_CONTRACT>

YOUR TASK:
Provide a concise, constructive review. 
- Carefully read the Integration Contract, paying special attention to the JSON schemas, the 'สิ่งที่ห้ามทำ' (Forbidden Actions) table, and the Node boundaries.
- If the code violates ANY of the rules, schemas, or constraints defined in the contract (e.g., Module 07 making network calls instead of Module 03, failing to return a LiveDataSnapshot in Module 04, modifying other modules' business logic), highlight the violation in **bold** and explain why it's a security/architecture risk.
- Do NOT hallucinate rules. Verify against the text of the contract. For instance, note that Module 03 handles tool execution/LLM network calls, while Module 07 is purely a prompt formatter/parser (Decision LLM).
- If the code looks safe and strictly follows the contract, state: '✅ **Approved: No architectural violations detected.**'
"""

    payload = {
        "model": "openai/gpt-oss-120b",
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
        with open("review_output.md", "w", encoding="utf-8") as f:
            f.write(review)
        print("Review successfully generated.")
    else:
        print(f"Error calling Groq API: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
