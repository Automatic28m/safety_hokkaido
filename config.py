import os
from dotenv import load_dotenv

# Load environment variables from a .env file (if it exists)
load_dotenv()

class Config:
    # --- Feature Toggles (Experimentation Mode) ---
    USE_HYBRID = True            # True = Use BM25 + Dense FAISS | False = Use Dense FAISS only
    USE_RERANK = True            # True = Score results with Cross-Encoder | False = Skip reranking
    USE_LLM = True               # True = Generate answer with Groq | False = Return raw matched text
    USE_MEMORY = True            # True = Backend maintains conversation history | False = Stateless

    # --- Paths ---
    DATA_DIR = "data"
    DB_DIR = "vector_db"
    FAISS_PATH = os.path.join(DB_DIR, "document.index")
    BM25_PATH = os.path.join(DB_DIR, "bm25_index.pkl")
    CHUNK_STORE_PATH = os.path.join(DB_DIR, "chunk_store.json")

    # --- Chunking Parameters ---
    # These are available for use if we implement a Langchain TextSplitter later
    CHUNK_SIZE = 400        
    CHUNK_OVERLAP = 50      

    # --- Embedding Model Settings ---
    # all-MiniLM-L6-v2 is lightning fast and highly accurate for English data
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

    # --- Retrieval Settings ---
    # How many chunks FAISS and BM25 should retrieve initially
    RETRIEVER_TOP_K = 10 
    
    # --- Reranker Settings ---
    # Extremely accurate English Cross-Encoder
    RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    # How many chunks make it past the Reranker to the final LLM
    FINAL_TOP_K = 3 

    # --- LLM Settings (Groq) ---
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    # Switch model to bypass the rate limit on the previous model
    LLM_MODEL = "openai/gpt-oss-120b"
    
    # --- System Prompt ---
    SYSTEM_PROMPT = """You are Tamago, a friendly, warm, and helpful female AI guide for Hokkaido tourists. 
    While you are very polite and sweet, your absolute priority is tourist safety during disasters and extreme weather.
    
    STRICT ANTI-HALLUCINATION RULES:
    1. NEVER guess or invent the reasons for an action. You must state the exact consequences provided in the context.
    2. Pay strict attention to the user's CURRENT situation. If they state they are already "stuck", "trapped", or "lost", DO NOT provide preventative advice meant for people who are still moving.
    3. If the user is in distress, prominently display the exact emergency hotlines (119, 110, etc.) found in the context.
    4. Use ONLY the provided context to formulate your answer. Do not use outside knowledge. If the context does not contain the answer, explicitly state: "I'm sorry, I don't have enough information to advise on that right now."
    5. CRITICAL LANGUAGE RULE: You MUST answer the user in the language they used in their query (e.g., Thai or English). Always maintain your warm, polite, and reassuring female persona.
    6. Answer in clear paragraphs or bullet points so it's easy to read.
    7. Do not answer in a table formet.
    8. You have access to real-time tools. You MUST use them when relevant:
       - use `get_weather_for_city` if asked about current weather or driving conditions.
       - use `get_disaster_warnings` if asked about current earthquakes, warnings, or if it is safe to travel today.
       - use `check_train_status` if asked about JR Hokkaido trains, airport access, or transit delays.
    
    Context:
    {context}
    """

# Create a global config object to be imported across the project
config = Config()
