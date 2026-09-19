class ConversationMemory:
    def __init__(self, max_history=6):
        """
        Stores the conversation history in the backend.
        max_history: Keep only the most recent N messages to avoid overflowing the LLM context.
        """
        self.history = []
        self.max_history = max_history
        
    def add_user_message(self, message: str):
        self.history.append({"role": "user", "content": message})
        self._trim_history()
        
    def add_ai_message(self, message: str):
        self.history.append({"role": "assistant", "content": message})
        self._trim_history()
        
    def get_history(self):
        return self.history
        
    def clear(self):
        self.history = []
        
    def _trim_history(self):
        if len(self.history) > self.max_history:
            # Keep the newest `max_history` items
            self.history = self.history[-self.max_history:]

# Global memory instance for the backend session
global_memory = ConversationMemory()
