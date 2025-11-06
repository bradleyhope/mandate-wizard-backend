"""User Memory Manager - Stub"""

class UserMemoryManager:
    def __init__(self):
        self.memory = {}
    
    def get_memory(self, user_id):
        return self.memory.get(user_id, {})
    
    def update_memory(self, user_id, data):
        self.memory[user_id] = data
