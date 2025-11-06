"""
GPT-5 Client Module
Provides GPT-5 client functionality
"""

from openai import OpenAI
import os

class GPT5Client:
    """GPT-5 Client wrapper"""
    
    def __init__(self, api_key: str = None):
        """Initialize GPT-5 client"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
    
    def chat_completion(self, messages, model="gpt-4", **kwargs):
        """
        Create a chat completion
        
        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to gpt-4)
            **kwargs: Additional arguments for the API
            
        Returns:
            API response
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
