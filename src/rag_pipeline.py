from src.embedding_model import EmbeddingModel
from src.hybrid_retriever import HybridRetriever
from src.rerankers import Reranker
from src.generator import Generator
from src.query_transform import QueryTransformer
from src.memory import global_memory
from config import config

class RAGPipeline:
    def __init__(self):
        print("Initializing Hokkaido RAG Pipeline components...")
        self.embedder = EmbeddingModel()
        self.retriever = HybridRetriever(self.embedder)
        
        # Respect the toggle switches in config.py
        if config.USE_RERANK:
            self.reranker = Reranker()
        else:
            self.reranker = None
            
        self.generator = Generator()
        self.transformer = QueryTransformer()
        print("RAG Pipeline is online and ready!")

    def ask(self, query: str, chat_history=None, enabled_agents=None):
        if enabled_agents is None:
            enabled_agents = {"weather": True, "disaster": True, "train": True}
            
        # DL05 Contextual Memory
        if config.USE_MEMORY:
            chat_history = global_memory.get_history()
            if chat_history:
                standalone_query = self.transformer.reformulate_query(query, chat_history)
                print(f"DL05 Reformulation: '{query}' -> '{standalone_query}'")
            else:
                standalone_query = query
        else:
            standalone_query = query
            
        # Step 0: Translate to English (Enterprise Multilingual Standard)
        english_query = self.transformer.translate_to_english(standalone_query)
        print(f"Language Router: '{standalone_query}' -> Translated to -> '{english_query}'")
        
        # Step 1: Retrieve Top 10 Candidate Chunks from FAISS + BM25 using the English Query!
        candidates = self.retriever.retrieve(english_query, top_k=config.RETRIEVER_TOP_K)
        
        # Step 2: Rerank and filter down to Top 3 absolute best chunks
        if self.reranker and config.USE_RERANK:
            final_chunks = self.reranker.rerank(english_query, candidates, top_k=config.FINAL_TOP_K)
        else:
            final_chunks = candidates[:config.FINAL_TOP_K]
            
        # Pass the original query + modified chat history to the LLM
        # We must append the query so the LLM sees it
        if config.USE_MEMORY:
            full_history = global_memory.get_history() + [{"role": "user", "content": query}]
        else:
            full_history = chat_history if chat_history else [{"role": "user", "content": query}]
            
        # Step 3: Send the Top 3 chunks + Original Foreign Question + History to Groq
        answer = self.generator.generate(query, final_chunks, full_history, enabled_agents)
        
        # Save to backend memory
        if config.USE_MEMORY:
            global_memory.add_user_message(query)
            global_memory.add_ai_message(answer)
            
        return answer
