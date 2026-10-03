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

    system_prompt = f"""You are a helpful Code Reviewer for the Safety Hokkaido project.
Review the following code diff for a Pull Request.

Focus your review on:
1. Standard coding practices, readability, and maintainability.
2. The general approach and logic of the changes.
3. Potential bugs or obvious errors.

You do NOT need to strictly enforce 100% alignment with the full architectural implementation plan. Use the provided context as a general guideline, but be lenient and constructive.

<GENERAL_CONTEXT>
{architecture_rules}
</GENERAL_CONTEXT>

YOUR TASK:
Provide a concise, constructive review focusing on code quality and approach. 
- Do not block or heavily penalize the PR for minor architectural deviations if the approach is fundamentally sound.
- Highlight any good practices used.
- Suggest improvements if the code approach can be optimized.
- If the code looks generally good and safe, state: '✅ **Approved: Code approach and standards look good.**'
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
