import os
import glob
import requests
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

data_dir = "/Volumes/Lexar/hokkaido_disaster_guide/data"
pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))

for file_path in pdf_files:
    filename = os.path.basename(file_path)
    
    try:
        reader = PdfReader(file_path)
        raw_text = ""
        if len(reader.pages) > 0:
            raw_text = reader.pages[0].extract_text()[:1000]
            
        # Decode the Caesar Cipher shift
        decoded_text = ''.join([chr(ord(c)-1) if 33 <= ord(c) <= 126 else c for c in raw_text])
        
        if not decoded_text.strip():
            print(f"Skipping {filename}: No text found.")
            continue
            
        payload = {
            'model': 'openai/gpt-oss-20b',
            'messages': [
                {'role': 'system', 'content': 'You are a file renamer. Based on the following text, figure out the main topic and return a concise, snake_case English filename ending in .pdf (e.g. japan_meteorological_tsunami_warning.pdf). Output ONLY the filename.'},
                {'role': 'user', 'content': decoded_text}
            ],
            'temperature': 0.1,
            'max_tokens': 500  # Give it enough room to think!
        }
        
        res = requests.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': f'Bearer {api_key}','Content-Type': 'application/json'}, json=payload)
        
        import time
        time.sleep(6)  # Avoid rate limits!
        
        if res.status_code != 200:
            print(f"Failed to call API for {filename}: {res.text}")
            continue
            
        new_name = res.json()["choices"][0]["message"]["content"].strip()
        new_name = new_name.replace(" ", "_").replace('"', '').replace("'", "").lower()
        new_name = new_name.split("\n")[-1] 
        
        if not new_name.endswith(".pdf"):
            new_name += ".pdf"
            
        # Prevent "_.pdf" or ".pdf"
        if len(new_name) < 5 or new_name == ".pdf":
            print(f"Failed to generate valid name for {filename}")
            continue
            
        new_path = os.path.join(data_dir, new_name)
        
        counter = 1
        original_new_name = new_name
        while os.path.exists(new_path) and new_path != file_path:
            name_part = original_new_name[:-4]
            new_name = f"{name_part}_{counter}.pdf"
            new_path = os.path.join(data_dir, new_name)
            counter += 1
            
        if file_path != new_path:
            os.rename(file_path, new_path)
            print(f"✅ Fixed: {filename} -> {new_name}")
            
    except Exception as e:
        print(f"❌ Error on {filename}: {e}")
