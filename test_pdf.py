import os
import glob
from pypdf import PdfReader

data_dir = "/Volumes/Lexar/hokkaido_disaster_guide/RAG-Project/data"
jp_files = glob.glob(os.path.join(data_dir, "スクリーンショット*.pdf"))

for f in jp_files:
    print(f"\n--- {os.path.basename(f)} ---")
    try:
        reader = PdfReader(f)
        text = reader.pages[0].extract_text()
        print(text[:200])
    except Exception as e:
        print(f"Error: {e}")
