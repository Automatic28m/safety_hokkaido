import os
import glob
import requests
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

data_dir = "/Volumes/Lexar/hokkaido_disaster_guide/data"
pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))

print(f"Found {len(pdf_files)} PDFs in {data_dir}")

for file_path in pdf_files:
    filename = os.path.basename(file_path)
    if not filename.startswith("スクリーンショット"):
        continue
        
    print(f"\nProcessing: {filename}")
    try:
        reader = PdfReader(file_path)
        text = ""
        if len(reader.pages) > 0:
            text = reader.pages[0].extract_text()[:1500]
            
        if not text.strip():
            print(f"Skipping {filename}: No text found.")
            continue
            
        payload = {
            'model': 'openai/gpt-oss-20b',
            'messages': [
                {'role': 'system', 'content': 'You are a file renamer. Based on the following text (which might be garbled due to PDF encoding), figure out the main topic of the document and return a concise, snake_case English filename ending in .pdf (maximum 5 words before the extension). For example: japan_heavy_snow_warning.pdf. Do NOT output any reasoning, ONLY the exact filename.'},
                {'role': 'user', 'content': text}
            ],
            'temperature': 0.1,
            'max_tokens': 50
        }
        
        res = requests.post('https://api.groq.com/openai/v1/chat/completions', headers={'Authorization': f'Bearer {api_key}','Content-Type': 'application/json'}, json=payload)
        new_name = res.json()["choices"][0]["message"]["content"].strip()
        
        # Clean up new_name just in case the LLM included weird characters
        new_name = new_name.replace(" ", "_").replace('"', '').replace("'", "").lower()
        # Remove any leading text before the actual snake_case string if LLM hallucinated
        new_name = new_name.split("\n")[-1] 
        
        if not new_name.endswith(".pdf"):
            new_name += ".pdf"
            
        new_path = os.path.join(data_dir, new_name)
        
        # Ensure we don't overwrite if the name already exists
        counter = 1
        original_new_name = new_name
        while os.path.exists(new_path):
            name_part = original_new_name[:-4]
            new_name = f"{name_part}_{counter}.pdf"
            new_path = os.path.join(data_dir, new_name)
            counter += 1
            
        os.rename(file_path, new_path)
        print(f"✅ Renamed -> {new_name}")
        
    except Exception as e:
        print(f"❌ Error on {filename}: {e}")
