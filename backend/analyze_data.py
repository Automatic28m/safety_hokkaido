import json
import os
from collections import Counter
from config import config

def analyze_distribution():
    chunk_store_path = config.CHUNK_STORE_PATH
    
    if not os.path.exists(chunk_store_path):
        print(f"Error: {chunk_store_path} not found. Please run build_index.py first.")
        return
        
    with open(chunk_store_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
        
    if not chunks:
        print("The chunk store is empty.")
        return
        
    total_chunks = len(chunks)
    situation_counter = Counter()
    file_counter = Counter()
    
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        # Grab the situation, default to "Unknown" if missing
        situation = metadata.get("situation", "Unknown")
        source_file = metadata.get("source_file", "Unknown")
        
        situation_counter[situation] += 1
        file_counter[source_file] += 1
        
    print(f"📊 --- Hokkaido Knowledge Database Analysis --- 📊")
    print(f"Total Searchable Chunks: {total_chunks}\n")
    
    print("=== Breakdown by SITUATION ===")
    for sit, count in situation_counter.most_common():
        percentage = (count / total_chunks) * 100
        # Print with a nice visual bar chart using blocks
        bar = "█" * int(percentage / 2)
        print(f"{percentage:05.2f}% | {bar:<50} | ({count} chunks) - {sit}")
        
    print("\n=== Breakdown by SOURCE FILE ===")
    for file, count in file_counter.most_common():
        percentage = (count / total_chunks) * 100
        print(f"{percentage:05.2f}% ({count} chunks) - {file}")

if __name__ == "__main__":
    analyze_distribution()
