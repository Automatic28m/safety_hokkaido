import re
with open("02_api_backend/api/endpoints.py", "r") as f:
    content = f.read()

replacement = """        res = requests.post(
            audit_url,
            json=payload,
            headers={"X-Node08-Token": audit_token},
            timeout=2.0
        )
        if res.status_code >= 400:
            logger.warning(f"Audit rejected: {res.text}")"""

content = re.sub(r'        requests.post\([\s\S]*?timeout=2\.0\n        \)', replacement, content)

with open("02_api_backend/api/endpoints.py", "w") as f:
    f.write(content)
